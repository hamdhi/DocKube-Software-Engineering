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
    onOpen: (String) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize().background(DocBackground),
        contentPadding = ScreenPadding,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            NoteCard(
                title = "Learning Centre",
                body = "Everything here works offline. Read a chapter, then copy any " +
                    "command out of it into an SSH client on your machine.",
            )
        }
        items(content.chapters, key = { it.title }) { chapter ->
            ChapterRow(chapter = chapter, onClick = { onOpen(chapter.title) })
        }
    }
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
 * Chapters ship as HTML because the desktop guide is full of comparison tables.
 * Reusing a WebView keeps those tables intact, which a Compose text renderer
 * would flatten into unreadable walls of text on a narrow phone screen.
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
</style></head>
<body><h1>$title</h1>
$body
</body></html>
""".trimIndent()