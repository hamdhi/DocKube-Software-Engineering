package com.dockeybe.mobile.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dockeybe.mobile.data.CommandRef
import com.dockeybe.mobile.data.DocKubeContent

/** One search hit, tagged with the category it came from. */
private data class Hit(val category: String, val command: CommandRef)

@Composable
fun SearchScreen(
    content: DocKubeContent,
    onCopy: (String) -> Unit,
    onShare: (String) -> Unit,
) {
    var query by remember { mutableStateOf("") }

    // Flatten once; searching 300+ commands on every keystroke is still cheap,
    // but this keeps the list stable while the text changes.
    val allHits = remember(content) {
        content.categories.flatMap { category ->
            category.allCommands.map { Hit(category.name, it) }
        }
    }
    val hits = remember(query, allHits) {
        if (query.isBlank()) {
            emptyList()
        } else {
            val needle = query.trim().lowercase()
            allHits.filter { hit ->
                hit.command.label.lowercase().contains(needle) ||
                    hit.command.command.lowercase().contains(needle) ||
                    hit.category.lowercase().contains(needle)
            }
        }
    }
Column(Modifier.fillMaxSize().background(DocBackground)) {
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            modifier = Modifier.fillMaxWidth().padding(ScreenPadding),
            placeholder = { Text("kubectl, docker, port-forward…", color = DocMuted) },
            leadingIcon = { Icon(Icons.Default.Search, null, tint = DocMuted) },
            singleLine = true,
            shape = RoundedCornerShape(10.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = DocText,
                unfocusedTextColor = DocText,
                focusedBorderColor = DocAccent,
                unfocusedBorderColor = DocBorder,
                cursorColor = DocAccent,
            ),
        )

        when {
            query.isBlank() -> {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text(
                        "Search all ${allHits.size} commands",
                        color = DocMuted,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Medium,
                    )
                }
            }

            hits.isEmpty() -> {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center,
                ) {
                    Text("Nothing matched \"$query\"", color = DocMuted, fontSize = 15.sp)
                }
            }

            else -> {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = ScreenPadding,
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    item {
                        Text(
                            "${hits.size} result${if (hits.size == 1) "" else "s"}",
                            color = DocMuted,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                        )
                    }
                    // Cap the list so a one-letter query cannot build a huge
                    // column and make the screen stutter.
                    items(
                        hits.take(250),
                        key = { "${it.category}|${it.command.label}|${it.command.command}" }
                    ) { hit ->
                        Card(
                            colors = CardDefaults.cardColors(containerColor = DocSurface),
                            shape = RoundedCornerShape(10.dp),
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Column(Modifier.padding(14.dp)) {
                                Text(
                                    hit.category.uppercase(),
                                    color = DocMuted,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                )
                                Text(
                                    hit.command.label,
                                    color = DocText,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    modifier = Modifier.padding(top = 2.dp),
                                )
                                Text(
                                    hit.command.command,
                                    color = DocAccent,
                                    fontFamily = FontFamily.Monospace,
                                    fontSize = 12.sp,
                                    modifier = Modifier.padding(top = 4.dp),
                                )
                                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                    TextButton(onClick = { onCopy(hit.command.command) }) {
                                        Text("Copy", color = DocAccent)
                                    }
                                    TextButton(onClick = { onShare(hit.command.command) }) {
                                        Text("Share", color = DocAccent)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}