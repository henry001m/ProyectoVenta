import 'package:flutter/material.dart';
import 'package:easy_localization/easy_localization.dart';
import 'core/routes/app_router.dart';
import 'core/theme/app_theme.dart';

class KicksInsightApp extends StatelessWidget {
  const KicksInsightApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp.router(title: 'Kicks Insight', theme: AppTheme.light, darkTheme: AppTheme.dark, routerConfig: AppRouter.router, debugShowCheckedModeBanner: false, localizationsDelegates: context.localizationDelegates, supportedLocales: context.supportedLocales, locale: context.locale);
}

