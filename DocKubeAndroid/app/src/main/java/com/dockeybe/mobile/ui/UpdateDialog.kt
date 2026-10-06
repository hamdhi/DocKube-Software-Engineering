package com.dockeybe.mobile.ui

import android.content.Context
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dockeybe.mobile.BuildConfig
import com.dockeybe.mobile.data.ReleaseInfo
import com.dockeybe.mobile.data.UpdateRepository
import com.dockeybe.mobile.data.UpdateResult
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/** What the dialog is currently doing. */
private sealed interface Phase {
    data object Checking : Phase
    data class Result(val outcome: UpdateResult) : Phase
    data class Downloading(val done: Long, val total: Long) : Phase
    data class HandOff(val message: String) : Phase
    data class Failed(val message: String) : Phase
}

/**
 * The Update button's dialog: checks GitHub, downloads the APK and hands it to
 * the system installer.
 *
 * Every network call runs on Dispatchers.IO and comes back to the composition,
 * so the dialog never blocks the UI thread.
 */
@Composable
fun UpdateDialog(onDismiss: () -> Unit) {
    val context: Context = LocalContext.current
    val scope = rememberCoroutineScope()
    var phase by remember { mutableStateOf<Phase>(Phase.Checking) }

    LaunchedEffect(Unit) {
        val outcome = withContext(Dispatchers.IO) { UpdateRepository.check(context) }
        phase = Phase.Result(outcome)
    }

    val outcome = (phase as? Phase.Result)?.outcome
    val download = phase as? Phase.Downloading
    // Both a proven newer build and an undecidable one offer the download.
    // Only "UpToDate" withholds it, because that is the only case where we
    // know installing would change nothing.
    val available = when (val result = outcome) {
        is UpdateResult.Available -> result.release
        is UpdateResult.Unknown -> result.release
        else -> null
    }

    AlertDialog(
        onDismissRequest = { if (download == null) onDismiss() },
        containerColor = DocSurfaceHigh,
        title = {
            Text(
                text = when {
                    phase is Phase.Checking -> "Checking for updates"
                    download != null -> "Downloading"
                    phase is Phase.HandOff -> "Almost done"
                    (outcome as? UpdateResult.Available) != null -> "Update available"
                    // "You are up to date" would be a claim we cannot make.
                    (outcome as? UpdateResult.Unknown) != null -> "Newest build unknown"
                    (outcome as? UpdateResult.Failed) != null -> "Update check failed"
                    else -> "You are up to date"
                },
                color = DocText,
                fontWeight = FontWeight.Bold,
            )
        },
        text = {
            Column {
                when {
                    phase is Phase.Checking -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(
                                modifier = Modifier.width(18.dp).height(18.dp),
                                color = DocAccent,
                                strokeWidth = 2.dp,
                            )
                            Spacer(Modifier.width(12.dp))
                            Text("Asking GitHub for the newest build.",
                                color = DocMuted, fontSize = 14.sp)
                        }
                    }

                    download != null -> {
                        // Determinate only when the server sent a length;
                        // otherwise an empty bar still moves, which reads as
                        // working rather than hung.
                        if (download.total > 0) {
                            LinearProgressIndicator(
                                progress = {
                                    (download.done.toFloat() / download.total).coerceIn(0f, 1f)
                                },
                                modifier = Modifier.fillMaxWidth(),
                                color = DocAccent,
                            )
                        } else {
                            LinearProgressIndicator(
                                modifier = Modifier.fillMaxWidth(),
                                color = DocAccent,
                            )
                        }
                        Spacer(Modifier.height(8.dp))
                        Text(progressCaption(download), color = DocMuted, fontSize = 14.sp)
                    }

                    else -> Text(
                        text = when (val current = phase) {
                            is Phase.Failed -> current.message
                            is Phase.HandOff -> current.message
                            is Phase.Result -> when (val result = current.outcome) {
                                is UpdateResult.Available -> describe(result.release)
                                is UpdateResult.UpToDate -> result.message
                                is UpdateResult.Unknown -> result.message
                                is UpdateResult.Failed -> result.message
                            }
                            else -> ""
                        },
                        color = DocMuted,
                        fontSize = 14.sp,
                    )
                }
            }
},
        confirmButton = {
            when {
                download != null -> TextButton(onClick = {}, enabled = false) {
                    Text("Downloading...", color = DocMuted)
                }
                phase is Phase.HandOff -> TextButton(onClick = onDismiss) {
                    Text("Done", color = DocAccent)
                }
                available != null -> {
                    Row {
                        TextButton(onClick = onDismiss) {
                            Text("Later", color = DocMuted)
                        }
                        TextButton(onClick = {
                            phase = Phase.Downloading(0, 0)
                            scope.launch {
                                install(context, available, scope, onDismiss) { phase = it }
                            }
                        }) {
                            Text("Download and install", color = DocAccent)
                        }
                    }
                }
                else -> TextButton(onClick = onDismiss) {
                    Text("Close", color = DocAccent)
                }
            }
        },
    )
}

/**
 * Download the APK and open the system installer over it.
 *
 * The digest is deliberately NOT recorded here. The system installer runs in
 * another process and can fail (signature mismatch) or be cancelled, and
 * recording the new digest first is what made the next check say "up to
 * date" while the old build was still installed. The digest is only recorded
 * when a version check proves the new build is actually on the device.
 *
 * Failures are reported through the same dialog rather than a toast, which
 * would have vanished before it could be read.
 */
private suspend fun install(
    context: Context,
    release: ReleaseInfo,
    scope: CoroutineScope,
    onDismiss: () -> Unit,
    onPhase: (Phase) -> Unit,
) {
    try {
        val apk = withContext(Dispatchers.IO) {
            UpdateRepository.download(context, release) { done, total ->
                // Dispatched to the main thread, because `phase` is Compose
                // state and may only be written from there.
                scope.launch { onPhase(Phase.Downloading(done, total)) }
            }
        }
        context.startActivity(UpdateRepository.installIntent(context, apk))
        // The installer is now in charge; the dialog stays open on a result
        // screen so a signature-mismatch failure is visible instead of the
        // app silently looking unchanged. If the user installs, Android
        // restarts the app into the new build by itself.
        val installed = runCatching {
            context.packageManager.getPackageInfo(context.packageName, 0)
        }.getOrNull()
        onPhase(
            Phase.HandOff(
                "The installer should now be open on top of DocKube.\n\n" +
                    "If it reports a signature or package mismatch, uninstall " +
                    "the old DocKube first (long-press its icon), then install " +
                    "this APK fresh — a debug-signed update cannot replace a " +
                    "differently-signed install.\n\n" +
                    "Currently installed: ${installed?.versionName ?: "unknown"}."
            )
        )
    } catch (exc: Exception) {
        onPhase(Phase.Failed(exc.message ?: "The update could not be downloaded"))
    }
}

/** Percent when the total is known, plain megabytes when it is not. */
private fun progressCaption(download: Phase.Downloading): String =
    if (download.total > 0) {
        "${download.done * 100 / download.total}%"
    } else {
        "${download.done / (1024 * 1024)} MB"
    }

/** The details shown when there really is something newer. */
private fun describe(release: ReleaseInfo): String {
    val uploaded = release.publishedAt.take(10).ifEmpty { "unknown date" }
    return "Installed: DocKube ${BuildConfig.VERSION_NAME}\n" +
        "Published: ${release.versionLabel}\n" +
        "Size: ${release.assetName} (${release.sizeMb} MB)\n" +
        "Uploaded: $uploaded"
}
