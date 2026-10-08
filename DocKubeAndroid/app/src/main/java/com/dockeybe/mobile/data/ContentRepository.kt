package com.dockeybe.mobile.data

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/**
 * Loads android_content.json from the APK's assets.
 *
 * The file is a few hundred kilobytes and is parsed once on first use, off the
 * main thread. Everything ships inside the APK, so the app works with no
 * network. The only exception is the update check, which has its own
 * repository in this package.
 */
object ContentRepository {

    private const val ASSET_NAME = "android_content.json"

    @Volatile
    private var cached: DocKubeContent? = null

    fun load(context: Context): DocKubeContent {
        cached?.let { return it }
        return synchronized(this) {
            cached ?: parse(context).also { cached = it }
        }
    }

    private fun parse(context: Context): DocKubeContent {
        val raw = context.assets.open(ASSET_NAME).use { it.readBytes().toString(Charsets.UTF_8) }
        val root = JSONObject(raw)

        val categoryNames = root.getJSONArray("categories").toStringList()
        val commandsJson = root.getJSONObject("commands")
        val docsJson = root.optJSONObject("docs")

        val categories = categoryNames.map { name ->
            val entry = commandsJson.optJSONObject(name) ?: JSONObject()
            CategoryContent(
                name = name,
                commands = entry.optJSONArray("commands").toCommandList(),
                groups = entry.optJSONArray("groups").toObjectList { group ->
                    CommandGroup(
                        title = group.optString("title"),
                        items = group.optJSONArray("items").toCommandList(),
                    )
                },
                doc = docsJson?.optString(name).orEmpty(),
            )
        }

        val chapters = root.getJSONArray("chapters").toObjectList { item ->
            Chapter(
                title = item.getString("title"),
                html = item.getString("html"),
            )
        }

        return DocKubeContent(categories = categories, chapters = chapters)
    }

    private fun JSONArray?.toStringList(): List<String> =
        if (this == null) emptyList() else (0 until length()).map { getString(it) }

    // optJSONArray returns null when a key is absent, and two categories on the
    // desktop app genuinely have no commands, so every reader tolerates null.
    private fun JSONArray?.toCommandList(): List<CommandRef> =
        if (this == null) {
            emptyList()
        } else {
            (0 until length()).map { index ->
                val item = getJSONObject(index)
                CommandRef(
                    label = item.optString("label"),
                    command = item.optString("command"),
                    arg = item.optBoolean("arg", false),
                    placeholder = if (item.has("placeholder")) {
                        item.optString("placeholder")
                    } else {
                        null
                    },
                    // Documentation entries carry "html" instead of "command".
                    html = if (item.has("html")) item.optString("html") else null,
                )
            }
        }

    private fun <T> JSONArray?.toObjectList(transform: (JSONObject) -> T): List<T> =
        if (this == null) emptyList() else (0 until length()).map { index ->
            transform(getJSONObject(index))
        }
}