import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'app/app.dart';
import 'app/core/di/service_locator.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await EasyLocalization.ensureInitialized();
  await configureDependencies();
  runApp(EasyLocalization(supportedLocales: const [Locale('es'), Locale('en'), Locale('zh')], path: 'assets/translations', fallbackLocale: const Locale('es'), child: const KicksInsightApp()));
}

