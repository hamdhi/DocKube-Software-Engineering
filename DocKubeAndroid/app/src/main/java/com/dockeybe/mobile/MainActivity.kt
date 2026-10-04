package com.dockeybe.mobile

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import com.dockeybe.mobile.data.ContentRepository
import com.dockeybe.mobile.data.DocKubeContent
import com.dockeybe.mobile.ui.DocBackground
import com.dockeybe.mobile.ui.DocRed
import com.dockeybe.mobile.ui.DocKubeApp
import com.dockeybe.mobile.ui.DocKubeTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            DocKubeTheme {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(DocBackground)
                ) {
                    AppRoot(context = this@MainActivity)
                }
            }
        }
    }
}

/**
 * Parsing a few hundred kilobytes of JSON is fast but not instant, so it runs
 * off the main thread and the first frame shows a spinner rather than a stall.
 */
@Composable
private fun AppRoot(context: Context) {
    var content by remember { mutableStateOf<DocKubeContent?>(null) }
    var failed by remember { mutableStateOf(false) }

    LaunchedEffect(context) {
        val loaded = withContext(Dispatchers.IO) {
            runCatching { ContentRepository.load(context) }
        }
        content = loaded.getOrNull()
        failed = loaded.isFailure
    }

    // contentAlignment centres the children; Modifier.align only exists inside
    // a Box's own scope, so it cannot be used from this function directly.
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        when {
            content != null -> DocKubeApp(content = content!!)
            failed -> Text(
                text = "Could not load the command library.",
                color = DocRed,
            )
            else -> CircularProgressIndicator()
        }
    }
}

