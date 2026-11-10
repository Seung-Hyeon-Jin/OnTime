import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/routine_model.dart';
import '../providers/routine_provider.dart';

class RoutineEditScreen extends StatefulWidget {
  final RoutineModel routine;

  const RoutineEditScreen({super.key, required this.routine});

  @override
  State<RoutineEditScreen> createState() => _RoutineEditScreenState();
}

class _RoutineEditScreenState extends State<RoutineEditScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _nameController;
  late TimeOfDay _departureTime;
  late Set<String> _selectedDays;
  late int _notifyMinsBefore;
  late bool _enabled;
  late bool _excludeHolidays;
  bool _isSaving = false;

  final List<Map<String, String>> _allDays = const [
    {'key': 'MON', 'label': '월'},
    {'key': 'TUE', 'label': '화'},
    {'key': 'WED', 'label': '수'},
    {'key': 'THU', 'label': '목'},
    {'key': 'FRI', 'label': '금'},
    {'key': 'SAT', 'label': '토'},
    {'key': 'SUN', 'label': '일'},
  ];

  final List<int> _notifyMinsOptions = const [5, 10, 15, 20, 30];

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(text: widget.routine.name);

    // Parse departure_time (HH:MM:SS)
    final timeParts = widget.routine.departureTime.split(':');
    final hour = timeParts.isNotEmpty ? int.tryParse(timeParts[0]) ?? 8 : 8;
    final minute = timeParts.length >= 2 ? int.tryParse(timeParts[1]) ?? 0 : 0;
    _departureTime = TimeOfDay(hour: hour, minute: minute);

    _selectedDays = Set<String>.from(widget.routine.scheduledDays);
    _notifyMinsBefore = widget.routine.notifyMinsBefore;
    _enabled = widget.routine.enabled;
    _excludeHolidays = widget.routine.excludeHolidays;
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _handleSave() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedDays.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('최소 하나 이상의 반복 요일을 선택해 주세요.')),
      );
      return;
    }

    setState(() => _isSaving = true);

    try {
      final routineProvider =
          Provider.of<RoutineProvider>(context, listen: false);

      final formattedTime =
          '${_departureTime.hour.toString().padLeft(2, '0')}:${_departureTime.minute.toString().padLeft(2, '0')}:00';

      final originMap = widget.routine.origin != null
          ? {
              'name': widget.routine.origin!.name,
              'latitude': widget.routine.origin!.latitude,
              'longitude': widget.routine.origin!.longitude,
              if (widget.routine.origin!.cityCode != null)
                'city_code': widget.routine.origin!.cityCode,
            }
          : null;

      final destMap = widget.routine.destination != null
          ? {
              'name': widget.routine.destination!.name,
              'latitude': widget.routine.destination!.latitude,
              'longitude': widget.routine.destination!.longitude,
              if (widget.routine.destination!.cityCode != null)
                'city_code': widget.routine.destination!.cityCode,
            }
          : null;

      await routineProvider.updateRoutine(
        routineId: widget.routine.routineId,
        name: _nameController.text.trim(),
        departureStop: widget.routine.departureStop,
        arrivalStop: widget.routine.arrivalStop,
        scheduledDays: _selectedDays.toList(),
        departureTime: formattedTime,
        notifyMinsBefore: _notifyMinsBefore,
        enabled: _enabled,
        excludeHolidays: _excludeHolidays,
        origin: originMap,
        destination: destMap,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('루틴 설정이 성공적으로 수정되었습니다.'),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('수정 실패: $e'),
            backgroundColor: const Color(0xFFF04438),
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }

  Future<void> _handleDeleteRoutine() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text('루틴 삭제'),
        content: Text('\'${widget.routine.name}\' 루틴을 정말 삭제하시겠습니까?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('취소', style: TextStyle(color: Color(0xFF8B95A1))),
          ),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('삭제',
                style: TextStyle(
                    color: Color(0xFFF04438), fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );

    if (confirm == true && mounted) {
      try {
        final routineProvider =
            Provider.of<RoutineProvider>(context, listen: false);
        await routineProvider.deleteRoutine(widget.routine.routineId);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: const Text('루틴이 정상적으로 삭제되었습니다.'),
              behavior: SnackBarBehavior.floating,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          );
          Navigator.pop(context);
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('루틴 삭제 실패: $e'),
              backgroundColor: const Color(0xFFF04438),
              behavior: SnackBarBehavior.floating,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    const tossBlue = Color(0xFF6C4DF6);
    const tossDarkText = Color(0xFF191F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F6),
      appBar: AppBar(
        title: const Text('루틴 수정'),
        centerTitle: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Info Card
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
                        '📌 루틴 기본 설정',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: tossDarkText,
                        ),
                      ),
                      const SizedBox(height: 16),
                      TextFormField(
                        controller: _nameController,
                        decoration: const InputDecoration(
                          labelText: '루틴 이름',
                          hintText: '루틴 이름을 입력해주세요',
                        ),
                        validator: (v) => v == null || v.trim().isEmpty
                            ? '루틴 이름을 입력해주세요'
                            : null,
                      ),
                      const SizedBox(height: 16),

                      // Origin & Destination Readonly Box
                      Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF9FAFB),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: const Color(0xFFE5E8EB)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: const BoxDecoration(
                                    color: tossBlue,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    '출발: ${widget.routine.departureStop}',
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: tossDarkText,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: const BoxDecoration(
                                    color: Color(0xFFF04438),
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    '도착: ${widget.routine.arrivalStop}',
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.bold,
                                      color: tossDarkText,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Schedule Days & Time Config Card
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
                        '⏰ 출발 정시 및 반복 요일',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: tossDarkText,
                        ),
                      ),
                      const SizedBox(height: 12),

                      // Departure Time Selection
                      Material(
                        color: Colors.transparent,
                        child: ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text(
                            '출발 정시 설정',
                            style: TextStyle(
                              fontSize: 14,
                              color: Color(0xFF4E5968),
                            ),
                          ),
                          subtitle: Text(
                            '${_departureTime.hour.toString().padLeft(2, '0')}:${_departureTime.minute.toString().padLeft(2, '0')}',
                            style: const TextStyle(
                              fontSize: 22,
                              fontWeight: FontWeight.bold,
                              color: tossBlue,
                            ),
                          ),
                          trailing: Container(
                            padding: const EdgeInsets.all(10),
                            decoration: const BoxDecoration(
                              color: Color(0xFFE8F3FF),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.access_time_filled_rounded,
                                color: tossBlue),
                          ),
                          onTap: () async {
                            final picked = await showTimePicker(
                              context: context,
                              initialTime: _departureTime,
                            );
                            if (picked != null) {
                              setState(() => _departureTime = picked);
                            }
                          },
                        ),
                      ),
                      const Divider(color: Color(0xFFF2F4F6), height: 24),

                      // Repeat Days Selection
                      const Text(
                        '반복 요일 선택',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF4E5968),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: _allDays.map((day) {
                          final isSelected = _selectedDays.contains(day['key']);
                          return FilterChip(
                            label: Text(day['label']!),
                            selected: isSelected,
                            onSelected: (selected) {
                              setState(() {
                                if (selected) {
                                  _selectedDays.add(day['key']!);
                                } else {
                                  _selectedDays.remove(day['key']);
                                }
                              });
                            },
                            selectedColor: tossBlue,
                            backgroundColor: const Color(0xFFF2F4F6),
                            side: BorderSide.none,
                            labelStyle: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: isSelected
                                  ? Colors.white
                                  : const Color(0xFF4E5968),
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),

                // Notification & Enable Config Card
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
                        '🔔 출발 정시 미리 알림 설정',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: tossDarkText,
                        ),
                      ),
                      const SizedBox(height: 6),
                      const Text(
                        '설정하신 출발 정시보다 몇 분 전에 미리 알림을 받으실지 선택하세요.',
                        style:
                            TextStyle(fontSize: 13, color: Color(0xFF8B95A1)),
                      ),
                      const SizedBox(height: 12),

                      Wrap(
                        spacing: 8,
                        children: _notifyMinsOptions.map((mins) {
                          final isSelected = _notifyMinsBefore == mins;
                          return ChoiceChip(
                            label: Text('$mins분 전'),
                            selected: isSelected,
                            onSelected: (selected) {
                              if (selected) {
                                setState(() => _notifyMinsBefore = mins);
                              }
                            },
                            selectedColor: const Color(0xFF31B057),
                            backgroundColor: const Color(0xFFF2F4F6),
                            side: BorderSide.none,
                            labelStyle: TextStyle(
                              fontWeight: FontWeight.bold,
                              color: isSelected
                                  ? Colors.white
                                  : const Color(0xFF4E5968),
                            ),
                          );
                        }).toList(),
                      ),
                      const Divider(color: Color(0xFFF2F4F6), height: 24),

                      // Exclude Holidays Switch
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text(
                          '공휴일엔 알림 받지 않기',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: tossDarkText,
                          ),
                        ),
                        subtitle: Text(
                          _excludeHolidays
                              ? '설날, 추석, 빨간날 등 공휴일에는 알림이 스킵됩니다.'
                              : '공휴일에도 지정된 요일/시각에 알림을 발송합니다.',
                          style: const TextStyle(
                              fontSize: 12, color: Color(0xFF8B95A1)),
                        ),
                        value: _excludeHolidays,
                        activeTrackColor: tossBlue,
                        onChanged: (val) {
                          setState(() => _excludeHolidays = val);
                        },
                      ),
                      const Divider(color: Color(0xFFF2F4F6), height: 24),

                      // Routine Enabled Switch
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text(
                          '이 루틴 활성화',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: tossDarkText,
                          ),
                        ),
                        subtitle: Text(
                          _enabled
                              ? '지정된 요일 및 시간에 알림을 수신합니다.'
                              : '이 루틴의 알림이 일시 중지됩니다.',
                          style: const TextStyle(
                              fontSize: 12, color: Color(0xFF8B95A1)),
                        ),
                        value: _enabled,
                        activeTrackColor: tossBlue,
                        onChanged: (val) {
                          setState(() => _enabled = val);
                        },
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 24),

                // Save Action Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isSaving ? null : _handleSave,
                    child: _isSaving
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('수정사항 저장하기'),
                  ),
                ),
                const SizedBox(height: 12),

                // Delete Action Button
                SizedBox(
                  width: double.infinity,
                  child: OutlinedButton.icon(
                    onPressed: _isSaving ? null : _handleDeleteRoutine,
                    icon: const Icon(Icons.delete_outline_rounded,
                        color: Color(0xFFF04438), size: 18),
                    label: const Text(
                      '이 루틴 삭제하기',
                      style: TextStyle(
                        color: Color(0xFFF04438),
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: Color(0xFFFEE2E2)),
                      backgroundColor: const Color(0xFFFEE2E2),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
