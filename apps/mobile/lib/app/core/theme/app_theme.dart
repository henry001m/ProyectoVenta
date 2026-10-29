import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData get light => ThemeData(colorSchemeSeed: Colors.orange, brightness: Brightness.light, useMaterial3: true, cardTheme: const CardThemeData(margin: EdgeInsets.zero));
  static ThemeData get dark => ThemeData(colorSchemeSeed: Colors.orange, brightness: Brightness.dark, useMaterial3: true, cardTheme: const CardThemeData(margin: EdgeInsets.zero));
}

