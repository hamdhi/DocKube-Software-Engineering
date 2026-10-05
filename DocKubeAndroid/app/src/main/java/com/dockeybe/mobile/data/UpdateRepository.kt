package com.dockeybe.mobile.data

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import com.dockeybe.mobile.BuildConfig
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.security.MessageDigest

/** The newest build published under the android-latest GitHub tag. */
data class ReleaseInfo(
    val tag: String,
    val assetName: String,
    val sizeBytes: Long,
    val sha256: String,
    val downloadUrl: String,
    val htmlUrl: String,
    val version: String?,
    val publishedAt: String,
) {
    val sizeMb: Long get() = sizeBytes / (1024 * 1024)

    /** A dotted version for display, or null when the release carries none. */
    val versionLabel: String get() = version ?: "unversioned build"
}

/** Outcome of an update check, already reduced to what the UI has to say. */
sealed interface UpdateResult {
    data class Available(val release: ReleaseInfo) : UpdateResult
    data class UpToDate(val message: String) : UpdateResult
    data class Failed(val message: String) : UpdateResult
}

/**
 * Checks GitHub for a newer APK and installs it.
 *
 * This is the only part of the app that touches the network. Everything else
 * reads from assets, which is why the content still works with no signal.
 *
 * The feed is a pinned tag rather than a version, so the newest build is
 * identified two ways: a version line stamped into the release body by the
 * publish workflow, and the asset's sha256 as a fallback for releases
 * published before that line existed.
 */
object UpdateRepository {

    private const val RELEASE_URL =
        "https://api.github.com/repos/hamdhi/DocKube-Software-Engineering" +
            "/releases/tags/android-latest"

    private const val PREF_DIGEST = "android_build_digest"
    private const val CHUNK = 64 * 1024

    private val VERSION_PATTERN = Regex("""v?(\d+\.\d+\.\d+)""")

    /**
     * Fetch the release and decide whether it is newer than what is installed.
     *
     * Blocking; call it from a coroutine on Dispatchers.IO. The digest of the
     * last seen build is remembered in shared preferences, because a first run
     * has nothing to compare against and must not invent an update.
     */
    fun check(context: Context): UpdateResult {
        val release = try {
            fetchLatest()
        } catch (exc: Exception) {
            return UpdateResult.Failed(exc.message ?: "Could not reach GitHub")
        }

        val current = BuildConfig.VERSION_NAME
        val knownDigest = prefs(context).getString(PREF_DIGEST, null)

        release.version?.let { remote ->
            val comparison = compareVersions(remote, current)
            if (comparison > 0) return UpdateResult.Available(release)
            if (comparison == 0) return UpdateResult.UpToDate("DocKube $current is already installed.")
        }

        if (!knownDigest.isNullOrEmpty() && release.sha256.isNotEmpty()) {
            return if (release.sha256 != knownDigest) {
                UpdateResult.Available(release)
            } else {
                UpdateResult.UpToDate("The published build matches the last one checked.")
            }
        }

        // Nothing to compare against, so say so rather than guessing.
        return UpdateResult.UpToDate(
            "This release carries no version number and there is no earlier " +
                "check to compare it against, so DocKube cannot tell whether " +
                "$current is the newest build."
        )
    }

    private fun fetchLatest(): ReleaseInfo {
        val connection = (URL(RELEASE_URL).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 15_000
            readTimeout = 15_000
            // GitHub rejects requests that carry no User-Agent.
            setRequestProperty("Accept", "application/vnd.github+json")
            setRequestProperty("User-Agent", "DocKube-Android")
        }
        try {
            val code = connection.responseCode
            if (code != HttpURLConnection.HTTP_OK) {
                throw IllegalStateException("GitHub returned HTTP $code")
            }
            val payload = connection.inputStream.bufferedReader().use { it.readText() }
            return parse(JSONObject(payload))
        } finally {
            connection.disconnect()
        }
    }
/** Pull the APK out of a release payload. Throws if there is not one. */
    fun parse(root: JSONObject): ReleaseInfo {
        val assets = root.optJSONArray("assets") ?: throw IllegalStateException(
            "The ${root.optString("tag_name", "release")} release has no files attached."
        )
        var asset: JSONObject? = null
        for (index in 0 until assets.length()) {
            val candidate = assets.optJSONObject(index) ?: continue
            if (candidate.optString("name", "").endsWith(".apk", ignoreCase = true)) {
                asset = candidate
                break
            }
        }
        asset ?: throw IllegalStateException("The release has no APK attached to it.")

        val body = root.optString("body", "")
        return ReleaseInfo(
            tag = root.optString("tag_name", ""),
            assetName = asset.optString("name", "update.apk"),
            sizeBytes = asset.optLong("size", 0L),
            sha256 = asset.optString("digest", "").removePrefix("sha256:").lowercase(),
            downloadUrl = asset.optString("browser_download_url", ""),
            htmlUrl = root.optString("html_url", ""),
            // The body is stamped by the workflow; the name is the older fallback.
            version = VERSION_PATTERN.find(body)?.groupValues?.get(1)
                ?: VERSION_PATTERN.find(root.optString("name", ""))?.groupValues?.get(1),
            publishedAt = root.optString("published_at", ""),
        )
    }

    /**
     * Compare two dotted versions. Returns 1, 0 or -1 for newer, same, older.
     *
     * Compared component by component as numbers, so 1.10.0 correctly beats
     * 1.9.0. A component that is not a number stops the comparison and
     * reports equality, which keeps a malformed value from being read as
     * something newer than it is.
     */
    fun compareVersions(remote: String, local: String): Int {
        val remoteParts = remote.trim().removePrefix("v").split('.')
        val localParts = local.trim().removePrefix("v").split('.')
        val width = maxOf(remoteParts.size, localParts.size)
        for (index in 0 until width) {
            val remotePart = remoteParts.getOrNull(index)?.trim()?.toIntOrNull() ?: return 0
            val localPart = localParts.getOrNull(index)?.trim()?.toIntOrNull() ?: return 0
            if (remotePart != localPart) return if (remotePart > localPart) 1 else -1
        }
        return 0
    }

    /**
     * Download the APK into the cache and verify it before it is offered to
     * the installer. Returns the downloaded file.
     *
     * A .part file is renamed only once the bytes check out, so an interrupted
     * download can never be handed to the package installer.
     */
    fun download(context: Context, release: ReleaseInfo, onProgress: (Long, Long) -> Unit): File {
        val folder = File(context.cacheDir, "updates").apply { mkdirs() }
        // Cleared first, otherwise a failed download would leave the previous
        // APK sitting there looking like a fresh one.
        folder.listFiles()?.forEach { it.delete() }
        val target = File(folder, release.assetName)
        val staging = File(folder, "${release.assetName}.part")

        val digest = MessageDigest.getInstance("SHA-256")
        var written = 0L
        val connection = (URL(release.downloadUrl).openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = 20_000
            readTimeout = 60_000
            setRequestProperty("User-Agent", "DocKube-Android")
            // GitHub redirects the asset to a CDN; without this the response
            // is a 302 body rather than the APK.
            instanceFollowRedirects = true
        }
        try {
            if (connection.responseCode != HttpURLConnection.HTTP_OK) {
                throw IllegalStateException("The download returned HTTP ${connection.responseCode}")
            }
            val total = connection.contentLengthLong
            connection.inputStream.use { input ->
                staging.outputStream().use { output ->
                    val buffer = ByteArray(CHUNK)
                    while (true) {
                        val read = input.read(buffer)
                        if (read <= 0) break
                        output.write(buffer, 0, read)
                        digest.update(buffer, 0, read)
                        written += read
                        onProgress(written, total)
                    }
                }
            }
            val actual = digest.digest().joinToString("") { "%02x".format(it) }
            if (release.sha256.isNotEmpty() && actual != release.sha256) {
                throw IllegalStateException(
                    "The download did not match the checksum GitHub published, so it was discarded."
                )
            }
            if (!staging.renameTo(target)) {
                throw IllegalStateException("Could not save the downloaded update")
            }
            return target
        } catch (exc: Exception) {
            staging.delete()
            throw exc
        } finally {
            connection.disconnect()
        }
    }

    /**
     * The intent that hands a downloaded APK to the system package installer.
     *
     * The file is exposed through the app's FileProvider because the installer
     * runs in another process and cannot read a file:// path on Android 7+.
     */
    fun installIntent(context: Context, apk: File): Intent {
        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", apk)
        return Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, "application/vnd.android.package-archive")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
    }

    /** Remember the build that was actually installed, for the next comparison. */
    fun rememberInstalled(context: Context, release: ReleaseInfo) {
        if (release.sha256.isNotEmpty()) {
            prefs(context).edit().putString(PREF_DIGEST, release.sha256).apply()
        }
    }

    private fun prefs(context: Context) =
        context.getSharedPreferences("dockeybe_prefs", Context.MODE_PRIVATE)
}
