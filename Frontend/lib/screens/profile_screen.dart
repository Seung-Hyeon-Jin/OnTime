import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/routine_model.dart';
import '../providers/auth_provider.dart';
import '../providers/routine_provider.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  RoutineModel? _selectedTestRoutine;
  bool _isTestingRoutine = false;
  bool _isUpdatingNotifications = false;

  Future<void> _toggleNotifications(bool enabled) async {
    if (_isUpdatingNotifications) return;
    setState(() => _isUpdatingNotifications = true);
    try {
      await context.read<AuthProvider>().updateNotificationsEnabled(enabled);
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('알림 설정 변경에 실패했습니다: $error')),
      );
    } finally {
      if (mounted) setState(() => _isUpdatingNotifications = false);
    }
  }

  Future<void> _runRoutineTest() async {
    final routine = _selectedTestRoutine;
    if (routine == null) return;

    setState(() => _isTestingRoutine = true);
    try {
      final routineProvider = context.read<RoutineProvider>();
      final execution = await routineProvider.executeRoutine(routine.routineId);
      await routineProvider.sendTestNotification(routine.routineId);
      if (!mounted) return;
      final arrivalCount = execution.route.segments
          .expand((segment) => segment.stops)
          .expand((stop) => stop.arrivals)
          .length;
      showDialog<void>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('루틴 테스트 완료'),
          content: Text(
            '${routine.name}\n'
            '${routine.departureStop} → ${routine.arrivalStop}\n\n'
            '실시간 도착 정보 $arrivalCount건을 확인했습니다.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('확인'),
            ),
          ],
        ),
      );
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('루틴 테스트에 실패했습니다: $error')),
      );
    } finally {
      if (mounted) setState(() => _isTestingRoutine = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    final user = auth.user;

    const tossBlue = Color(0xFF6C4DF6);
    const tossDarkText = Color(0xFF191F28);

    final routineProvider = context.watch<RoutineProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFFF7F5FF),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            SafeArea(
              bottom: false,
              child: Padding(
                padding: const EdgeInsets.only(top: 8.0, bottom: 16.0),
                child: const Text(
                  '마이페이지',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                    color: tossDarkText,
                    fontFamily: 'Pretendard',
                    letterSpacing: -0.5,
                  ),
                ),
              ),
            ),
            // User Header Toss Card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: const Color(0xFFEDE9FF),
                    child: Text(
                      (user?.name.isNotEmpty == true)
                          ? user!.name[0].toUpperCase()
                          : 'U',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                        color: tossBlue,
                      ),
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          user?.name ?? '사용자',
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: tossDarkText,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          user?.email ?? '이메일 정보 없음',
                          style: const TextStyle(
                            fontSize: 13,
                            color: Color(0xFF8B95A1),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
              ),
              child: SwitchListTile(
                contentPadding: EdgeInsets.zero,
                secondary: const Icon(Icons.notifications_active_outlined,
                    color: tossBlue),
                title: const Text(
                  '알림 받기',
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                subtitle: Text(
                  user?.notificationsEnabled == true
                      ? '루틴 출발 및 실시간 교통 알림을 받습니다.'
                      : '모든 루틴 알림이 일시 중지되었습니다.',
                  style:
                      const TextStyle(fontSize: 12, color: Color(0xFF8B95A1)),
                ),
                value: user?.notificationsEnabled ?? true,
                onChanged:
                    _isUpdatingNotifications ? null : _toggleNotifications,
              ),
            ),
            const SizedBox(height: 16),

            // App Information Toss Card
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(24),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '서비스 정보',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: tossDarkText,
                    ),
                  ),
                  const SizedBox(height: 12),
                  _buildInfoRow('앱 버전', 'v1.0.0 (시연용)'),
                  const Divider(height: 24, color: Color(0xFFF2F4F6)),
                  _buildInfoRow('실시간 연동', '서울시/국토부/ODsay/카카오 API'),
                  const Divider(height: 24, color: Color(0xFFF2F4F6)),
                  _buildInfoRow('알림 서비스', '실시간 환승 모니터링 활성화'),
                ],
              ),
            ),
            const SizedBox(height: 24),

            _buildRoutineTestCard(routineProvider),
            const SizedBox(height: 24),

            ...[
              SizedBox(
                width: double.infinity,
                child: TextButton.icon(
                  onPressed: () async {
                    await auth.logout();
                    if (context.mounted) {
                      Navigator.of(context, rootNavigator: true)
                          .pushAndRemoveUntil(
                        MaterialPageRoute(builder: (_) => const LoginScreen()),
                        (route) => false,
                      );
                    }
                  },
                  icon: const Icon(Icons.logout_rounded,
                      color: Color(0xFFF04438)),
                  label: const Text(
                    '로그아웃',
                    style: TextStyle(
                      color: Color(0xFFF04438),
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  style: TextButton.styleFrom(
                    backgroundColor: const Color(0xFFFEE2E2),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 14,
            color: Color(0xFF4E5968),
          ),
        ),
        Text(
          value,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: Color(0xFF191F28),
          ),
        ),
      ],
    );
  }

  Widget _buildRoutineTestCard(RoutineProvider routineProvider) {
    const tossBlue = Color(0xFF6C4DF6);
    final selectedRoutine = routineProvider.routines
        .where(
            (routine) => routine.routineId == _selectedTestRoutine?.routineId)
        .firstOrNull;
    final initialRoutine =
        selectedRoutine ?? routineProvider.routines.firstOrNull;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFFFDFCFF), Color(0xFFEDE8FF)],
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFFBFAFFF)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.science_rounded, color: tossBlue),
              SizedBox(width: 8),
              Text(
                '루틴 알림 테스트',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            '루틴을 선택하고 테스트 실행을 누르면 실제 푸시 알림을 발송합니다.',
            style: TextStyle(fontSize: 13, color: Color(0xFF6B7280)),
          ),
          const SizedBox(height: 14),
          if (routineProvider.routines.isEmpty)
            const Text(
              '테스트할 루틴이 없습니다.',
              style: TextStyle(color: Color(0xFF8A86A0)),
            )
          else ...[
            DropdownButtonFormField<RoutineModel>(
              key: ValueKey(
                routineProvider.routines
                    .map((routine) => routine.routineId)
                    .join(','),
              ),
              initialValue: initialRoutine,
              decoration: const InputDecoration(
                labelText: '테스트할 루틴',
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              ),
              items: routineProvider.routines
                  .map(
                    (routine) => DropdownMenuItem(
                      value: routine,
                      child: Text(
                        routine.name,
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  )
                  .toList(),
              onChanged: _isTestingRoutine
                  ? null
                  : (routine) => setState(() => _selectedTestRoutine = routine),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isTestingRoutine ||
                        context
                                .read<AuthProvider>()
                                .user
                                ?.notificationsEnabled !=
                            true
                    ? null
                    : _runRoutineTest,
                icon: _isTestingRoutine
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.play_arrow_rounded),
                label: Text(_isTestingRoutine ? '조회 중...' : '테스트 실행'),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
