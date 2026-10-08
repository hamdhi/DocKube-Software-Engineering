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
import androidx.compose.material.icons.filled.ContentCopy
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
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.lazy.LazyListState
import com.dockeybe.mobile.data.Chapter as LearningChapter
import com.dockeybe.mobile.data.DocKubeContent
import kotlinx.coroutines.launch

/** Where the app currently is. */
sealed interface Screen {
    data object Home : Screen
    data class Category(val name: String) : Screen
    data object ChapterList : Screen
    data class Chapter(val chapter: LearningChapter) : Screen
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

    // Scroll state for home, the chapter list and category pages is hoisted here
    // so it survives navigating away and re-entering. Hoisting the whole
    // LazyListState (not just an index) is what makes back-navigation restore:
    // seeding with initialFirstVisibleItemIndex inside each screen re-created
    // the state on return, and the snapshotFlow collector wrote 0 over the
    // saved index before the restore ran, dumping the user at the top.
    // LazyListState.Saver keeps index + offset across recompositions, and per
    // category key keeps each category's position separate.
    val homeListState = rememberSaveable(saver = LazyListState.Saver) {
        LazyListState()
    }
    val chapterListState = rememberSaveable(saver = LazyListState.Saver) {
        LazyListState()
    }
    // One LazyListState per category, saved across recompositions AND process
    // death. A plain remember map was wiped whenever the app state changed,
    // which dumped the user back at the top of the category list.
    val categoryListStates = rememberSaveable(
        saver = listSaver(
            save = { states ->
                states.entries.map { (name, state) ->
                    "${name.length}:$name:${state.firstVisibleItemIndex}:${state.firstVisibleItemScrollOffset}"
                }
            },
            restore = { saved ->
                saved.mapNotNull { entry ->
                    val firstColon = entry.indexOf(':')
                    if (firstColon < 0) return@mapNotNull null
                    val nameLen = entry.substring(0, firstColon).toIntOrNull()
                        ?: return@mapNotNull null
                    val nameStart = firstColon + 1
                    val name = entry.substring(nameStart, nameStart + nameLen)
                    val rest = entry.substring(nameStart + nameLen + 1)
                    val parts = rest.split(':')
                    val index = parts.getOrNull(0)?.toIntOrNull() ?: 0
                    val offset = parts.getOrNull(1)?.toIntOrNull() ?: 0
                    name to LazyListState(index, offset)
                }.toMap().toMutableMap()
            },
        )
    ) { mutableMapOf<String, LazyListState>() }
    fun categoryState(name: String): LazyListState =
        categoryListStates.getOrPut(name) { LazyListState() }

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
                            is Screen.ChapterList -> "Networking Masterclass"
                            is Screen.Chapter -> s.chapter.title
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
                actions = {
                    val selected = screen
                    if (selected is Screen.Chapter) {
                        selected.chapter.copyText?.let { guideText ->
                            IconButton(onClick = { copyText(guideText) }) {
                                Icon(
                                    Icons.Default.ContentCopy,
                                    contentDescription = "Copy ${selected.chapter.title}",
                                    tint = DocAccent,
                                )
                            }
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
                    listState = homeListState,
                    onCategory = { screen = Screen.Category(it) },
                    onLearning = { screen = Screen.ChapterList },
                    onSearch = { screen = Screen.Search },
                    onUpdate = { showUpdate = true },
                )

                is Screen.Category -> {
                    val category = content.categories.firstOrNull { it.name == s.name }
                    if (category == null) screen = Screen.Home
                    else CategoryScreen(
                        category = category,
                        listState = categoryState(s.name),
                        onCopy = copyText,
                        onShare = shareText,
                        onLearning = { screen = Screen.ChapterList },
                    )
                }

                is Screen.ChapterList -> ChapterListScreen(
                    content = content,
                    listState = chapterListState,
                    onOpen = { screen = Screen.Chapter(it) },
                )

                is Screen.Chapter -> ChapterScreen(chapter = s.chapter)

                is Screen.Search -> SearchScreen(
                    content = content,
                    onCopy = copyText,
                    onShare = shareText,
                )
            }
        }
    }
}