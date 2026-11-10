import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';

import 'providers/auth_provider.dart';
import 'providers/routine_provider.dart';
import 'providers/route_search_provider.dart';
import 'providers/arrival_provider.dart';

import 'screens/splash_screen.dart';
import 'services/push_notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!kIsWeb) {
    try {
      await Firebase.initializeApp().timeout(
        const Duration(seconds: 3),
        onTimeout: () {
          debugPrint('Firebase initialization timed out');
          return Firebase.app();
        },
      );
    } catch (e) {
      debugPrint('Firebase initialization error: $e');
    }

    try {
      await PushNotificationService.instance.initialize().timeout(
        const Duration(seconds: 3),
        onTimeout: () {
          debugPrint('PushNotificationService initialization timed out');
        },
      );
    } catch (e) {
      debugPrint('PushNotificationService initialization error: $e');
    }
  }
  runApp(const TransportApp());
}

class TransportApp extends StatelessWidget {
  const TransportApp({super.key});

  static const Color tossBlue = Color(0xFF6C4DF6);
  static const Color tossBackground = Color(0xFFF7F5FF);
  static const Color tossDarkText = Color(0xFF24213A);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProxyProvider<AuthProvider, RoutineProvider>(
          create: (_) => RoutineProvider(''),
          update: (_, auth, previous) {
            if (previous != null) {
              previous.updateToken(auth.token ?? '');
              return previous;
            }
            return RoutineProvider(auth.token ?? '');
          },
        ),
        ChangeNotifierProxyProvider<AuthProvider, RouteSearchProvider>(
          create: (_) => RouteSearchProvider(''),
          update: (_, auth, previous) => RouteSearchProvider(auth.token ?? ''),
        ),
        ChangeNotifierProxyProvider<AuthProvider, ArrivalProvider>(
          create: (_) => ArrivalProvider(''),
          update: (_, auth, previous) => ArrivalProvider(auth.token ?? ''),
        ),
      ],
      child: MaterialApp(
        title: 'OnTime',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          useMaterial3: true,
          fontFamily: 'Pretendard',
          fontFamilyFallback: const [
            'Pretendard Variable',
            'Pretendard',
            'Noto Sans KR',
            'Apple SD Gothic Neo',
            'sans-serif',
          ],
          splashFactory: InkRipple.splashFactory,
          scaffoldBackgroundColor: tossBackground,
          colorScheme: ColorScheme.fromSeed(
            seedColor: tossBlue,
            primary: tossBlue,
            secondary: const Color(0xFFFFB84D),
            surface: Colors.white,
          ),
          textTheme: GoogleFonts.notoSansKrTextTheme(
            Theme.of(context).textTheme,
          ).apply(
            bodyColor: tossDarkText,
            displayColor: tossDarkText,
            fontFamily: 'Pretendard',
          ),
          appBarTheme: const AppBarTheme(
            centerTitle: false,
            elevation: 0,
            scrolledUnderElevation: 0,
            backgroundColor: tossBackground,
            foregroundColor: tossDarkText,
            titleTextStyle: TextStyle(
              color: tossDarkText,
              fontSize: 20,
              fontWeight: FontWeight.bold,
              fontFamily: 'Pretendard',
            ),
          ),
          cardTheme: CardThemeData(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            color: Colors.white,
          ),
          inputDecorationTheme: InputDecorationTheme(
            filled: true,
            fillColor: const Color(0xFFF9FAFB),
            contentPadding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: BorderSide.none,
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(color: Color(0xFFE5E8EB)),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(color: tossBlue, width: 2),
            ),
            labelStyle: const TextStyle(color: Color(0xFF8A86A0)),
          ),
          elevatedButtonTheme: ElevatedButtonThemeData(
            style: ElevatedButton.styleFrom(
              backgroundColor: tossBlue,
              foregroundColor: Colors.white,
              elevation: 0,
              padding: const EdgeInsets.symmetric(vertical: 16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              textStyle: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        home: const SplashScreen(),
      ),
    );
  }
}
