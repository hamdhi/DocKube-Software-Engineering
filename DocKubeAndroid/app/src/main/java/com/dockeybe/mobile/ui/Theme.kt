package com.dockeybe.mobile.ui

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// The DocKube desktop palette, so the phone app looks like the same product.
val DocBackground = Color(0xFF0D1117)
val DocSurface = Color(0xFF161B22)
val DocSurfaceHigh = Color(0xFF1F2630)
val DocAccent = Color(0xFF58A6FF)
val DocText = Color(0xFFD4D4D4)
val DocMuted = Color(0xFF8B949E)
val DocGreen = Color(0xFF3FB950)
val DocRed = Color(0xFFF85149)
val DocBorder = Color(0xFF30363D)

private val DocKubeColors = darkColorScheme(
    primary = DocAccent,
    onPrimary = Color(0xFF06131F),
    secondary = DocMuted,
    background = DocBackground,
    onBackground = DocText,
    surface = DocSurface,
    onSurface = DocText,
    surfaceVariant = DocSurfaceHigh,
    onSurfaceVariant = DocText,
    outline = DocBorder,
    error = DocRed,
)

@Composable
fun DocKubeTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        val window = (view.context as Activity).window
        WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
    }
    MaterialTheme(
        colorScheme = DocKubeColors,
        content = content,
    )
}