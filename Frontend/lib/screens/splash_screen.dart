import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../providers/routine_provider.dart';
import 'login_screen.dart';
import 'main_navigation_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _animController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;
  String _statusText = '앱을 시작하는 중...';
  bool _isRetryable = false;

  @override
  void initState() {
    super.initState();

    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _fadeAnimation = CurvedAnimation(
      parent: _animController,
      curve: Curves.easeIn,
    );

    _scaleAnimation = Tween<double>(begin: 0.85, end: 1.0).animate(
      CurvedAnimation(
        parent: _animController,
        curve: Curves.easeOutBack,
      ),
    );

    _animController.forward();
    _initializeApp();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  Future<void> _initializeApp() async {
    AutoLoginResult result = AutoLoginResult.noSession;
    String? retryMessage;
    final minSplashDuration =
        Future.delayed(const Duration(milliseconds: 1000));

    try {
      final auth = Provider.of<AuthProvider>(context, listen: false);

      if (mounted) {
        setState(() {
          _isRetryable = false;
          _statusText = '자동 로그인 정보 확인 중...';
        });
      }

      // 1. 자동 로그인 (일시적 오류는 재시도 가능 상태로 돌려받음)
      result = await auth.tryAutoLogin();
      if (result == AutoLoginResult.retryable) {
        retryMessage = auth.errorMessage;
      }

      if (result == AutoLoginResult.authenticated && mounted) {
        setState(() {
          _statusText = '실시간 루틴 정보 불러오는 중...';
        });

        // 2. fetchRoutines (최대 3초 타임아웃 제한)
        final routineProvider =
            Provider.of<RoutineProvider>(context, listen: false);
        await routineProvider.fetchRoutines().timeout(
              const Duration(seconds: 3),
              onTimeout: () {},
            );
      }
    } catch (e) {
      debugPrint('Splash initialization error: $e');
    }

    await minSplashDuration;

    if (!mounted) return;

    if (result == AutoLoginResult.retryable) {
      setState(() {
        _isRetryable = true;
        _statusText = retryMessage ?? '네트워크 연결을 확인해 주세요.';
      });
      return;
    }

    if (result == AutoLoginResult.authenticated) {
      _navigateTo(const MainNavigationScreen());
    } else {
      _navigateTo(const LoginScreen());
    }
  }

  void _retryAutoLogin() {
    if (!mounted || !_isRetryable) return;
    setState(() {
      _isRetryable = false;
      _statusText = '다시 시도하는 중...';
    });
    _initializeApp();
  }

  void _navigateTo(Widget page) {
    Navigator.of(context).pushReplacement(
      PageRouteBuilder(
        pageBuilder: (context, animation, secondaryAnimation) => page,
        transitionsBuilder: (context, animation, secondaryAnimation, child) {
          return FadeTransition(opacity: animation, child: child);
        },
        transitionDuration: const Duration(milliseconds: 350),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const tossBlue = Color(0xFF6C4DF6);

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
        child: Stack(
          children: [
            Center(
              child: FadeTransition(
                opacity: _fadeAnimation,
                child: ScaleTransition(
                  scale: _scaleAnimation,
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Toss Style App Logo Tile
                      Container(
                        width: 96,
                        height: 96,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF6C4DF6), Color(0xFF4A2AC7)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(28),
                          boxShadow: [
                            BoxShadow(
                              color: tossBlue.withValues(alpha: 0.3),
                              blurRadius: 24,
                              offset: const Offset(0, 10),
                            ),
                          ],
                        ),
                        child: const Icon(
                          Icons.directions_bus_filled_rounded,
                          size: 50,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 24),
                      // App Title
                      const Text(
                        'OnTime',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.w800,
                          color: Color(0xFF191F28),
                          letterSpacing: -0.5,
                        ),
                      ),
                      const SizedBox(height: 8),
                      // App Tagline
                      const Text(
                        '출퇴근·등교 대중교통 루틴 알림',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                          color: Color(0xFF8B95A1),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            // Bottom Progress & Status Text
            Positioned(
              bottom: 56,
              left: 0,
              right: 0,
              child: Column(
                children: [
                  if (_isRetryable)
                    SizedBox(
                      width: 160,
                      child: ElevatedButton(
                        onPressed: _retryAutoLogin,
                        child: const Text('다시 시도'),
                      ),
                    )
                  else
                    const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        color: tossBlue,
                      ),
                    ),
                  const SizedBox(height: 16),
                  AnimatedSwitcher(
                    duration: const Duration(milliseconds: 300),
                    child: Text(
                      _statusText,
                      key: ValueKey<String>(_statusText),
                      style: const TextStyle(
                        fontSize: 13,
                        color: Color(0xFF8B95A1),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
