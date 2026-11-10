import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/routine_provider.dart';
import '../widgets/routine_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      Provider.of<RoutineProvider>(context, listen: false).fetchRoutines();
    });
  }

  @override
  Widget build(BuildContext context) {
    final routineProvider = Provider.of<RoutineProvider>(context);

    const tossBlue = Color(0xFF6C4DF6);
    const tossDarkText = Color(0xFF191F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF7F5FF),
      body: RefreshIndicator(
        onRefresh: () => routineProvider.fetchRoutines(),
        color: tossBlue,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 20.0, vertical: 8.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SafeArea(
                bottom: false,
                child: Padding(
                  padding: const EdgeInsets.only(top: 8.0, bottom: 16.0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: tossBlue,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Icon(
                              Icons.access_time_filled_rounded,
                              color: Colors.white,
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 10),
                          const Text(
                            'OnTime',
                            style: TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.w900,
                              color: tossDarkText,
                              letterSpacing: -0.5,
                            ),
                          ),
                        ],
                      ),

                    ],
                  ),
                ),
              ),

              const Text(
                '실시간 대중교통 루틴',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: tossDarkText,
                ),
              ),
              const SizedBox(height: 12),

              // Routine List or Empty State
              if (routineProvider.isLoading)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 40.0),
                  child: Center(
                    child: CircularProgressIndicator(color: tossBlue),
                  ),
                )
              else if (routineProvider.routines.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(24),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(24),
                    boxShadow: [
                      BoxShadow(
                        color: tossBlue.withValues(alpha: 0.08),
                        blurRadius: 16,
                        offset: const Offset(0, 6),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: const BoxDecoration(
                          color: Color(0xFFF0EDFF),
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(
                          Icons.add_road_rounded,
                          size: 36,
                          color: tossBlue,
                        ),
                      ),
                      const SizedBox(height: 16),
                      const Text(
                        '등록된 출퇴근 루틴이 없어요',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: tossDarkText,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '매일 이용하는 대중교통 경로를 등록하면\n실시간 버스·지하철 도착 정보가 여기에 표시됩니다.',
                        style: TextStyle(
                          fontSize: 13,
                          color: Color(0xFF8A86A0),
                          height: 1.4,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                )
              else
                Builder(
                  builder: (context) {
                    final routines = [...routineProvider.routines]
                      ..sort((left, right) {
                        if (left.enabled == right.enabled) return 0;
                        return left.enabled ? -1 : 1;
                      });
                    return ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: routines.length,
                      itemBuilder: (ctx, i) => RoutineCard(routine: routines[i]),
                    );
                  },
                ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }
}
