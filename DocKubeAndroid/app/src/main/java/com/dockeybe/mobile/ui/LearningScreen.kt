package com.dockeybe.mobile.ui

import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import com.dockeybe.mobile.data.Chapter
import com.dockeybe.mobile.data.DocKubeContent

@Composable
fun ChapterListScreen(
    content: DocKubeContent,
    listState: LazyListState,
    onOpen: (Chapter) -> Unit,
) {
    val guides = content.categories
        .firstOrNull { it.name == "Learning Guides" }
        ?.commands
        .orEmpty()
        .mapNotNull { guide ->
            guide.html?.let { Chapter(guide.label, markdownToHtml(it), copyText = it) }
        }

    // listState is hoisted at the app level and survives opening a chapter, so
    // going back restores the list exactly where it was.

    LazyColumn(
        state = listState,
        modifier = Modifier.fillMaxSize().background(DocBackground),
        contentPadding = ScreenPadding,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            NoteCard(
                title = "Networking Masterclass",
                body = "Master networking and practical programming in one offline " +
                    "library. Choose a chapter or open a programming guide below.",
            )
        }
        item(key = "masterclass-heading") { LearningSectionHeader("Masterclass Chapters") }
        items(content.chapters, key = { it.title }) { chapter ->
            ChapterRow(
                chapter = chapter,
                onClick = { onOpen(chapter) },
            )
        }
        if (guides.isNotEmpty()) {
            item(key = "programming-guides-heading") {
                LearningSectionHeader("Programming Guides")
            }
            items(guides, key = { "guide-${it.title}" }) { guide ->
                ChapterRow(chapter = guide, onClick = { onOpen(guide) })
            }
        }
    }
}

@Composable
private fun LearningSectionHeader(title: String) {
    androidx.compose.material3.Text(
        text = title,
        color = DocMuted,
        fontSize = 12.sp,
        fontWeight = FontWeight.Bold,
        modifier = Modifier.padding(top = 10.dp),
    )
}

@Composable
private fun ChapterRow(chapter: Chapter, onClick: () -> Unit) {
    Card(
        colors = CardDefaults.cardColors(containerColor = DocSurface),
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(chapter.title, color = DocText, fontWeight = FontWeight.SemiBold)
                val minutes = (chapter.html.length / 1400).coerceAtLeast(1)
                Text("~$minutes min read", color = DocMuted, fontSize = 12.sp)
            }
            Text("›", color = DocMuted, fontSize = 22.sp)
        }
    }
}

/**
 * Masterclass chapters ship as HTML; programming guides ship as Markdown.
 * Rendering both in a styled WebView preserves tables and code on phone screens.
 */
@Composable
fun ChapterScreen(chapter: Chapter) {
    val html = remember(chapter.html) { wrapForDisplay(chapter.title, chapter.html) }
    AndroidView(
        factory = { context ->
            WebView(context).apply {
                // toArgb(), not Color.value: value is a packed ULong, so
                // casting it to Int would hand WebView a nonsense colour.
                setBackgroundColor(DocBackground.toArgb())
                webViewClient = WebViewClient()
                // The app is offline by design, so never let content reach out.
                settings.javaScriptEnabled = false
                settings.allowFileAccess = false
                settings.allowContentAccess = false
                loadDataWithBaseURL(null, html, "text/html", "UTF-8", null)
            }
        },
        modifier = Modifier.fillMaxSize().background(DocBackground),
    )
}

/** Wrap the chapter fragment in a page that matches the DocKube palette. */
private fun wrapForDisplay(title: String, body: String): String = """
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  body { background:#0D1117; color:#D4D4D4; margin:0; padding:16px;
         font-family:-apple-system,Roboto,'Segoe UI',sans-serif; line-height:1.6;
         font-size:15px; word-wrap:break-word; }
  h1,h2,h3,h4 { color:#58A6FF; line-height:1.3; }
  h1 { font-size:22px; } h2 { font-size:19px; } h3 { font-size:17px; }
  p, li { font-size:15px; }
  a { color:#58A6FF; }
  code { background:#161B22; color:#79C0FF; padding:2px 5px; border-radius:4px;
         font-family:'Courier New',monospace; font-size:13px;
         word-break:break-all; }
  pre { background:#161B22; border:1px solid #30363D; border-radius:8px;
        padding:12px; overflow-x:auto; }
  pre code { background:none; padding:0; color:#D4D4D4; }
  table { width:100%; border-collapse:collapse; margin:12px 0;
          display:block; overflow-x:auto; font-size:13px; }
  th, td { border:1px solid #30363D; padding:8px 10px; text-align:left;
           vertical-align:top; min-width:90px; }
  th { background:#1F6FEB; color:#FFFFFF; font-weight:bold; }
  tr:nth-child(even) td { background:#161B22; }
  ul, ol { padding-left:22px; }
  strong { color:#FFFFFF; }
  hr { border:0; border-top:1px solid #30363D; margin:18px 0; }
</style></head>
<body><h1>${title.escapeHtml()}</h1>
$body
</body></html>
""".trimIndent()

private fun markdownToHtml(markdown: String): String {
    val output = StringBuilder()
    val paragraph = mutableListOf<String>()
    var listTag: String? = null
    var inCodeBlock = false

    fun flushParagraph() {
        if (paragraph.isNotEmpty()) {
            output.append("<p>")
                .append(paragraph.joinToString("<br>") { it.toInlineHtml() })
                .append("</p>")
            paragraph.clear()
        }
    }

    fun closeList() {
        listTag?.let { output.append("</").append(it).append(">") }
        listTag = null
    }

    val lines = markdown.lines()
    var index = 0
    while (index < lines.size) {
        val line = lines[index]
        val trimmed = line.trim()

        if (trimmed.startsWith("```")) {
            flushParagraph()
            closeList()
            if (inCodeBlock) output.append("</code></pre>") else output.append("<pre><code>")
            inCodeBlock = !inCodeBlock
            index++
            continue
        }
        if (inCodeBlock) {
            output.append(line.escapeHtml()).append('\n')
            index++
            continue
        }

        val heading = Regex("^(#{1,6})\\s+(.+)$").matchEntire(trimmed)
        if (heading != null) {
            flushParagraph()
            closeList()
            val level = heading.groupValues[1].length
            output.append("<h").append(level).append(">")
                .append(heading.groupValues[2].toInlineHtml())
                .append("</h").append(level).append(">")
            index++
            continue
        }

        if (trimmed.contains('|') && lines.getOrNull(index + 1)?.let(::isTableSeparator) == true) {
            flushParagraph()
            closeList()
            output.append("<table><thead><tr>")
            trimmed.toTableCells().forEach { output.append("<th>").append(it.toInlineHtml()).append("</th>") }
            output.append("</tr></thead><tbody>")
            index += 2
            while (index < lines.size && lines[index].trim().contains('|')) {
                output.append("<tr>")
                lines[index].trim().toTableCells().forEach {
                    output.append("<td>").append(it.toInlineHtml()).append("</td>")
                }
                output.append("</tr>")
                index++
            }
            output.append("</tbody></table>")
            continue
        }

        val unordered = Regex("^\\s*[-*+]\\s+(.+)$").matchEntire(line)
        val ordered = Regex("^\\s*\\d+[.)]\\s+(.+)$").matchEntire(line)
        val item = unordered ?: ordered
        if (item != null) {
            flushParagraph()
            val tag = if (unordered != null) "ul" else "ol"
            if (listTag != tag) {
                closeList()
                output.append("<").append(tag).append(">")
                listTag = tag
            }
            output.append("<li>").append(item.groupValues[1].toInlineHtml()).append("</li>")
            index++
            continue
        }

        if (trimmed.isEmpty()) {
            flushParagraph()
            closeList()
        } else {
            closeList()
            paragraph.add(trimmed)
        }
        index++
    }

    flushParagraph()
    closeList()
    if (inCodeBlock) output.append("</code></pre>")
    return output.toString()
}

private fun isTableSeparator(line: String): Boolean =
    line.trim().contains('|') && line.trim().trim('|').split('|')
        .all { cell -> cell.trim().matches(Regex(":?-{3,}:?")) }

private fun String.toTableCells(): List<String> =
    trim().removePrefix("|").removeSuffix("|").split('|').map(String::trim)

private fun String.toInlineHtml(): String =
    escapeHtml()
        .replace(Regex("`([^`]+)`"), "<code>$1</code>")
        .replace(Regex("\\*\\*(.+?)\\*\\*"), "<strong>$1</strong>")
        .replace(Regex("__(.+?)__"), "<strong>$1</strong>")
        .replace(Regex("\\*(.+?)\\*"), "<em>$1</em>")
        .replace(Regex("_(.+?)_"), "<em>$1</em>")
        .replace(
            Regex("\\[([^\\]]+)]\\((https?://[^)]+)\\)"),
            "<a href=\"$2\">$1</a>",
        )

private fun String.escapeHtml(): String =
    replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")