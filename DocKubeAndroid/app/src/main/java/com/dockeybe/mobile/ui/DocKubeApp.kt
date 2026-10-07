package com.dockeybe.mobile.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.dockeybe.mobile.data.DocKubeContent
import kotlinx.coroutines.launch

/** Where the app currently is. */
sealed interface Screen {
    data object Home : Screen
    data class Category(val name: String) : Screen
    data object ChapterList : Screen
    data class Chapter(val title: String) : Screen
    data object Search : Screen
}

val ScreenPadding = PaddingValues(16.dp)

fun copyToClipboard(context: Context, text: String) {
    val manager = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
    manager.setPrimaryClip(ClipData.newPlainText("DocKube command", text))
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DocKubeApp(content: DocKubeContent) {
    var screen by remember { mutableStateOf<Screen>(Screen.Home) }
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    // The update dialog floats over whichever screen is open, so the button
    // works from anywhere without adding a navigation destination for it.
    var showUpdate by remember { mutableStateOf(false) }
    if (showUpdate) {
        UpdateDialog(onDismiss = { showUpdate = false })
    }

    // Scroll positions for home, the chapter list and category pages are kept
    // alive at the app level so they survive navigating away and re-entering.
    // Each list seeds rememberLazyListState with its saved index (so restoring
    // cannot race a LaunchedEffect) and collects firstVisibleItemIndex to keep
    // the value current however the user leaves the screen.
    var homeScrollIndex by rememberSaveable { mutableStateOf(-1) }
    var chapterListScrollIndex by rememberSaveable { mutableStateOf(-1) }
    var categoryScrollIndex by rememberSaveable { mutableStateOf(-1) }

    // One definition of "go back", shared by the toolbar arrow and the system
    // back gesture. A chapter returns to the chapter list because that is
    // where it was chosen from; everything else returns to the home screen.
    val goBack: () -> Unit = {
        screen = when (screen) {
            is Screen.Chapter -> Screen.ChapterList
            else -> Screen.Home
        }
    }

    // Without this the system back gesture exits the app from anywhere,
    // because there is no back stack for Compose to pop. Registered only off
    // the home screen, so back still closes the app from the top.
    BackHandler(enabled = screen !is Screen.Home) { goBack() }

    // Copy and share are needed on several screens, so define them once here.
    val copyText: (String) -> Unit = { text ->
        copyToClipboard(context, text)
        scope.launch { snackbar.showSnackbar("Copied to clipboard") }
    }
    val shareText: (String) -> Unit = { text ->
        context.startActivity(
            Intent.createChooser(
                Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, text)
                },
                "Share command"
            )
        )
    }
Scaffold(
        containerColor = DocBackground,
        snackbarHost = { SnackbarHost(snackbar) },
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = when (val s = screen) {
                            is Screen.Home -> "DocKube"
                            is Screen.Category -> s.name
                            is Screen.ChapterList -> "Learning Centre"
                            is Screen.Chapter -> s.title
                            is Screen.Search -> "Search commands"
                        },
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        fontWeight = FontWeight.Bold,
                        fontSize = 18.sp,
                    )
                },
                navigationIcon = {
                    if (screen !is Screen.Home) {
                        IconButton(onClick = goBack) {
                            Icon(
                                Icons.AutoMirrored.Filled.ArrowBack,
                                contentDescription = "Back",
                                tint = DocAccent,
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DocSurface,
                    titleContentColor = DocText,
                ),
            )
        },
    ) { padding ->
        Box(modifier = Modifier.padding(padding).fillMaxSize()) {
            when (val s = screen) {
                is Screen.Home -> HomeScreen(
                    content = content,
                    onCategory = { screen = Screen.Category(it) },
                    onLearning = { screen = Screen.ChapterList },
                    onSearch = { screen = Screen.Search },
                    onUpdate = { showUpdate = true },
                    onScrollIndexChanged = { homeScrollIndex = it },
                    savedScrollIndex = homeScrollIndex,
                )

                is Screen.Category -> {
                    val category = content.categories.firstOrNull { it.name == s.name }
                    if (category == null) screen = Screen.Home
                    else CategoryScreen(
                        category = category,
                        onCopy = copyText,
                        onShare = shareText,
                        onLearning = { screen = Screen.ChapterList },
                        onScrollIndexChanged = { categoryScrollIndex = it },
                        savedScrollIndex = categoryScrollIndex,
                    )
                }

                is Screen.ChapterList -> ChapterListScreen(
                    content = content,
                    onOpen = { screen = Screen.Chapter(it) },
                    onScrollIndexChanged = { chapterListScrollIndex = it },
                    savedScrollIndex = chapterListScrollIndex,
                )

                is Screen.Chapter -> {
                    val chapter = content.chapters.firstOrNull { it.title == s.title }
                    if (chapter == null) screen = Screen.ChapterList
                    else ChapterScreen(chapter = chapter)
                }

                is Screen.Search -> SearchScreen(
                    content = content,
                    onCopy = copyText,
                    onShare = shareText,
                )
            }
        }
    }
}