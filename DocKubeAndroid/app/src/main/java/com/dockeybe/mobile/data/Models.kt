package com.dockeybe.mobile.data

/**
 * Data model for DocKube's content.
 *
 * The shape mirrors android_content.json, which export_android_content.py
 * produces by driving the desktop app itself. That keeps the phone's command
 * list from drifting away from the desktop one.
 */

data class CommandRef(
    val label: String,
    val command: String,
    val arg: Boolean = false,
    val placeholder: String? = null,
)

data class CommandGroup(
    val title: String,
    val items: List<CommandRef>,
)

data class CategoryContent(
    val name: String,
    val commands: List<CommandRef>,
    val groups: List<CommandGroup>,
    val doc: String,
) {
    /** Everything in this category, flattened for display and search. */
    val allCommands: List<CommandRef>
        get() = commands + groups.flatMap { it.items }

    val totalCommands: Int
        get() = allCommands.size
}

data class Chapter(
    val title: String,
    val html: String,
)

data class DocKubeContent(
    val categories: List<CategoryContent>,
    val chapters: List<Chapter>,
) {
    companion object {
        /** Categories that only make sense with a live cluster on a desktop. */
        val REFERENCE_ONLY = setOf("Custom", "Networking Masterclass")
    }
}