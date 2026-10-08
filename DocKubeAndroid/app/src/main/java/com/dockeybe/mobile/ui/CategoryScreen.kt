package com.dockeybe.mobile.ui

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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.foundation.lazy.LazyListState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dockeybe.mobile.data.CategoryContent
import com.dockeybe.mobile.data.CommandRef

@Composable
fun CategoryScreen(
    category: CategoryContent,
    listState: LazyListState,
    onCopy: (String) -> Unit,
    onShare: (String) -> Unit,
    onLearning: () -> Unit,
) {
    // listState is hoisted per category at the app level and survives
    // navigating away, so going back restores the position.

    // "Custom" is a free-text box on the desktop and "Networking Masterclass"
    // is only a launcher, so neither has commands worth listing here.
    if (category.name == "Networking Masterclass") {
        LearningLauncher(onLearning = onLearning)
        return
    }
    if (category.name == "Custom") {
        NoteCard(
            title = "Type your own commands",
            body = "On the desktop app this section runs a command you write yourself. " +
                "On your phone, keep commands in the clipboard and paste them into any " +
                "SSH client, or search the full list.",
        )
        return
    }
    // "Learning Guides" are documentation pages, not shell commands: each
    // entry carries rendered text in `html` instead of a `command`.
    if (category.name == "Learning Guides") {
        GuideList(category = category, listState = listState, onCopy = onCopy)
        return
    }

    LazyColumn(
        state = listState,
        modifier = Modifier.fillMaxSize().background(DocBackground),
        contentPadding = ScreenPadding,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        if (category.doc.isNotBlank()) {
            item { NoteCard(title = category.name, body = category.doc) }
        }

        if (category.commands.isNotEmpty()) {
            item { GroupHeader("Commands") }
            items(category.commands.size) { index ->
                CommandCard(
                    command = category.commands[index],
                    onCopy = onCopy,
                    onShare = onShare,
                )
            }
        }

        category.groups.forEach { group ->
            item(key = "header-${group.title}") { GroupHeader(group.title) }
            items(group.items.size) { index ->
                CommandCard(
                    command = group.items[index],
                    onCopy = onCopy,
                    onShare = onShare,
                )
            }
        }
    }
}

@Composable
private fun GroupHeader(title: String) {
    Text(
        text = title.uppercase(),
        color = DocMuted,
        fontSize = 12.sp,
        fontWeight = FontWeight.Bold,
        modifier = Modifier.padding(top = 8.dp, bottom = 2.dp),
    )
}

@Composable
fun CommandCard(
    command: CommandRef,
    onCopy: (String) -> Unit,
    onShare: (String) -> Unit,
) {
    val destructive = command.label.contains("DESTROY", ignoreCase = true) ||
        command.label.lowercase().startsWith("delete")
    Card(
        colors = CardDefaults.cardColors(containerColor = DocSurface),
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(start = 14.dp, end = 6.dp, top = 10.dp, bottom = 10.dp)) {
            Text(
                command.label,
                color = if (destructive) DocRed else DocText,
                fontWeight = FontWeight.SemiBold,
                fontSize = 14.sp,
            )
            Spacer(Modifier.height(6.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = command.command,
                    color = DocAccent,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 12.sp,
                    modifier = Modifier.weight(1f).padding(end = 4.dp),
                )
                IconButton(onClick = { onCopy(command.command) }) {
                    Icon(
                        Icons.Default.ContentCopy,
                        contentDescription = "Copy ${command.label}",
                        tint = DocMuted,
                    )
                }
                IconButton(onClick = { onShare(command.command) }) {
                    Icon(
                        Icons.Default.Share,
                        contentDescription = "Share ${command.label}",
                        tint = DocMuted,
                    )
                }
            }
            if (command.arg) {
                Text(
                    text = "Takes an argument: replace the placeholder before you run it.",
                    color = DocMuted,
                    fontSize = 11.sp,
                )
            }
        }
    }
}

@Composable
private fun GuideList(
    category: CategoryContent,
    listState: LazyListState,
    onCopy: (String) -> Unit,
) {
    LazyColumn(
        state = listState,
        modifier = Modifier.fillMaxSize().background(DocBackground),
        contentPadding = ScreenPadding,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        if (category.doc.isNotBlank()) {
            item { NoteCard(title = category.name, body = category.doc) }
        }
        items(category.commands.size) { index ->
            GuideCard(guide = category.commands[index], onCopy = onCopy)
        }
    }
}

@Composable
private fun GuideCard(
    guide: CommandRef,
    onCopy: (String) -> Unit,
) {
    // Tapping toggles the full guide text inline; `html` already holds the
    // rendered markdown, and the state resets per list row as you scroll.
    var expanded by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf(false) }
    Card(
        colors = CardDefaults.cardColors(containerColor = DocSurface),
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier.fillMaxWidth().clickable { expanded = !expanded },
    ) {
        Column(Modifier.padding(start = 14.dp, end = 6.dp, top = 10.dp, bottom = 10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    guide.label,
                    color = DocText,
                    fontWeight = FontWeight.SemiBold,
                    fontSize = 14.sp,
                    modifier = Modifier.weight(1f),
                )
                Icon(
                    Icons.Default.MenuBook,
                    contentDescription = if (expanded) "Collapse ${guide.label}" else "Read ${guide.label}",
                    tint = DocMuted,
                )
            }
            Text(
                text = if (expanded) "Tap to collapse" else "Tap to read the full guide",
                color = DocMuted,
                fontSize = 11.sp,
            )
            if (expanded) {
                Spacer(Modifier.height(6.dp))
                Text(
                    text = guide.html.orEmpty(),
                    color = DocText,
                    fontFamily = FontFamily.Monospace,
                    fontSize = 12.sp,
                )
                Spacer(Modifier.height(6.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Spacer(Modifier.weight(1f))
                    IconButton(onClick = { onCopy(guide.html.orEmpty()) }) {
                        Icon(
                            Icons.Default.ContentCopy,
                            contentDescription = "Copy ${guide.label}",
                            tint = DocMuted,
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun NoteCard(title: String, body: String) {
    Card(
        colors = CardDefaults.cardColors(containerColor = DocSurfaceHigh),
        shape = RoundedCornerShape(12.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Column(Modifier.padding(14.dp)) {
            Text(title, color = DocAccent, fontWeight = FontWeight.Bold, fontSize = 16.sp)
            Spacer(Modifier.height(6.dp))
            Text(body, color = DocText, fontSize = 14.sp)
        }
    }
}

@Composable
private fun LearningLauncher(
    onLearning: () -> Unit,
) {
    Column(Modifier.fillMaxSize().padding(16.dp)) {
        NoteCard(
            title = "Networking Masterclass",
            body = "Forty-plus chapters covering IP addresses, subnetting, ports, " +
                "TCP vs UDP, protocols, network devices, the Linux command line, " +
                "software engineering, sysadmin, DevOps, Docker, testing, " +
                "Python, AI, and more.",
        )
        Spacer(Modifier.height(12.dp))
        Card(
            colors = CardDefaults.cardColors(containerColor = DocAccent),
            shape = RoundedCornerShape(10.dp),
            modifier = Modifier.fillMaxWidth().clickable(onClick = onLearning),
        ) {
            Row(
                Modifier.padding(14.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center,
            ) {
                Icon(Icons.Default.MenuBook, null, tint = Color(0xFF06131F))
                Spacer(Modifier.width(8.dp))
                Text(
                    "Open the Learning Centre",
                    color = Color(0xFF06131F),
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}