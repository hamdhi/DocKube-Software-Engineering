plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.dockeybe.mobile"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.dockeybe.mobile"
        minSdk = 24
        // API 36 is Android 16, which is what the Redmi 14 Pro 4G runs.
        targetSdk = 36
        // versionCode must rise for the package installer to accept an update;
        // Android refuses to install over the same or a lower code.
        versionCode = 4
        versionName = "1.3.0"
    }

    buildTypes {
        release {
            // Debug-signed so the APK installs by sideloading. Swap in a real
            // keystore before publishing anywhere.
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"),
                          "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        // BuildConfig carries versionName and versionCode, which the update
        // check compares against the version GitHub publishes.
        buildConfig = true
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.12.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.10.0")
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.webkit:webkit:1.14.0")
    debugImplementation("androidx.compose.ui:ui-tooling")
}