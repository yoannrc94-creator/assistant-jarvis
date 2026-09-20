package com.jarvis.assistant

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val textView = TextView(this)
        textView.text = "Bonjour, je suis Jarvis. Ceci est la première version de test."
        textView.textSize = 20f
        setContentView(textView)
    }
}
