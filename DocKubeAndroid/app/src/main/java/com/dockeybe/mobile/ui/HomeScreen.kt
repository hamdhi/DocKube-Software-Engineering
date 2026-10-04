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
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dockeybe.mobile.data.CategoryContent
import com.dockeybe.mobile.data.DocKubeContent

@Composable
fun HomeScreen(
    content: DocKubeContent,
    onCategory: (String) -> Unit,
    onLearning: () -> Unit,
    onSearch: () -> Unit,
) {
    val totalCommands = content.categories.sumOf { it.totalCommands }
    LazyColumn(
        modifier = Modifier.fillMaxSize().background(DocBackground),
        contentPadding = ScreenPadding,
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Card(
                colors = CardDefaults.cardColors(containerColor = DocSurfaceHigh),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text(
                        "Your offline DevOps reference",
                        color = DocText,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "${content.categories.size} categories, $totalCommands commands " +
                            "and ${content.chapters.size} study chapters. " +
                            "Tap any command to copy it.",
                        color = DocMuted,
                        fontSize = 14.sp,
                    )
                    Spacer(Modifier.height(14.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        ActionChip(
                            icon = Icons.Default.Search,
                            label = "Search",
                            onClick = onSearch,
                            modifier = Modifier.weight(1f),
                        )
                        ActionChip(
                            icon = Icons.Default.MenuBook,
                            label = "Learn",
                            onClick = onLearning,
                            modifier = Modifier.weight(1f),
                        )
                    }
                }
            }
        }

        item {
            Text(
                "COMMANDS",
                color = DocMuted,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(top = 10.dp),
            )
        }

        items(content.categories, key = { it.name }) { category ->
            CategoryRow(category = category, onClick = { onCategory(category.name) })
        }
    }
}

@Composable
private fun ActionChip(
    icon: ImageVector,
    label: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = DocAccent),
        shape = RoundedCornerShape(10.dp),
        modifier = modifier.clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier.padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(icon, contentDescription = null, tint = Color(0xFF06131F))
            Spacer(Modifier.width(8.dp))
            Text(label, color = Color(0xFF06131F), fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun CategoryRow(category: CategoryContent, onClick: () -> Unit) {
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
                Text(category.name, color = DocText, fontWeight = FontWeight.SemiBold)
                Text(
                    if (category.totalCommands > 0) {
                        "${category.totalCommands} commands"
                    } else {
                        "Study material"
                    },
                    color = DocMuted,
                    fontSize = 12.sp,
                )
            }
            if (category.totalCommands > 0) {
                Text("›", color = DocMuted, fontSize = 22.sp)
            }
        }
    }
}