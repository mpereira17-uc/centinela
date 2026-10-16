plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "co.centinela.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "co.centinela.app"
        // Android 10: el filtro de llamadas sabe si la llamada entra o sale y puede silenciarla
        minSdk = 29
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

// Compila con el Java que traiga Android Studio (17 o más nuevo) y genera código para Java 17
kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("androidx.activity:activity-ktx:1.10.1")

    testImplementation("junit:junit:4.13.2")
    // org.json viene con Android, pero no en las pruebas que corren en la JVM
    testImplementation("org.json:json:20240303")
}
