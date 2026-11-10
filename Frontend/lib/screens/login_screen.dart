import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../providers/routine_provider.dart';
import 'main_navigation_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isLoginMode = true;
  final _formKey = GlobalKey<FormState>();

  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final auth = Provider.of<AuthProvider>(context, listen: false);
    try {
      if (_isLoginMode) {
        await auth.login(
          _nameController.text.trim(),
          _passwordController.text,
        );
      } else {
        await auth.register(
          _emailController.text.trim(),
          _nameController.text.trim(),
          _passwordController.text,
        );
      }

      if (mounted) {
        final routineProvider =
            Provider.of<RoutineProvider>(context, listen: false);
        routineProvider.fetchRoutines();
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => const MainNavigationScreen(),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            title: Row(
              children: const [
                Icon(Icons.error_outline_rounded,
                    color: Color(0xFFF04438), size: 24),
                SizedBox(width: 8),
                Text(
                  '로그인 실패',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF191F28),
                  ),
                ),
              ],
            ),
            content: const Text(
              '아이디 또는 비밀번호가 옳지 않습니다.\n입력하신 정보를 다시 확인해주세요.',
              style: TextStyle(fontSize: 14, color: Color(0xFF4E5968)),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text(
                  '확인',
                  style: TextStyle(
                    color: Color(0xFF6C4DF6),
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                  ),
                ),
              ),
            ],
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    const tossBlue = Color(0xFF6C4DF6);

    return Scaffold(
      backgroundColor: const Color(0xFFF7F5FF),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding:
                const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Toss Style App Logo & Big Header
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: const Color(0xFFEDE9FF),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(
                    Icons.directions_subway_rounded,
                    size: 32,
                    color: tossBlue,
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'OnTime',
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                    height: 1.3,
                    color: Color(0xFF191F28),
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  '대중교통 루틴 알림',
                  style: TextStyle(
                    fontSize: 14,
                    color: Color(0xFF8B95A1),
                  ),
                ),
                const SizedBox(height: 32),

                // Toss Card Form
                Container(
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                  ),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Email Field (Register Mode Only)
                        if (!_isLoginMode) ...[
                          const Text(
                            '이메일 주소',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF4E5968),
                            ),
                          ),
                          const SizedBox(height: 6),
                          TextFormField(
                            controller: _emailController,
                            decoration: const InputDecoration(
                              hintText: 'example@email.com',
                            ),
                            textInputAction: TextInputAction.next,
                            keyboardType: TextInputType.emailAddress,
                            validator: (val) {
                              if (val == null || !val.contains('@')) {
                                return '올바른 이메일 주소를 입력해주세요';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 16),
                        ],

                        // Username / ID Field
                        Text(
                          _isLoginMode ? '아이디 (이름 또는 이메일)' : '사용자 이름 (아이디)',
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF4E5968),
                          ),
                        ),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _nameController,
                          decoration: InputDecoration(
                            hintText: _isLoginMode
                                ? '이름 또는 이메일을 입력하세요'
                                : '사용자 이름을 입력하세요',
                          ),
                          textInputAction: TextInputAction.next,
                          onFieldSubmitted: (_) => _submit(),
                          validator: (val) {
                            if (val == null || val.trim().isEmpty) {
                              return '아이디를 입력해주세요';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),

                        // Password Field
                        const Text(
                          '비밀번호',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF4E5968),
                          ),
                        ),
                        const SizedBox(height: 6),
                        TextFormField(
                          controller: _passwordController,
                          decoration: const InputDecoration(
                            hintText: '비밀번호 입력',
                          ),
                          obscureText: true,
                          textInputAction: TextInputAction.done,
                          onFieldSubmitted: (_) => _submit(),
                          validator: (val) {
                            if (val == null || val.length < 4) {
                              return '비밀번호는 최소 4자 이상이어야 합니다';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 28),

                        // Main Action Button (Login / Register)
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton(
                            onPressed: auth.isLoading ? null : _submit,
                            child: auth.isLoading
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2,
                                      color: Colors.white,
                                    ),
                                  )
                                : Text(_isLoginMode ? '로그인하기' : '회원가입 완료하기'),
                          ),
                        ),
                        const SizedBox(height: 16),

                        // Subtle Link under Login Button to Switch to Register / Login Page
                        Center(
                          child: TextButton(
                            onPressed: () {
                              setState(() {
                                _isLoginMode = !_isLoginMode;
                              });
                            },
                            child: Text(
                              _isLoginMode
                                  ? '아직 계정이 없으신가요? 회원가입'
                                  : '이미 계정이 있으신가요? 로그인',
                              style: const TextStyle(
                                fontSize: 13,
                                color: Color(0xFF8B95A1),
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
