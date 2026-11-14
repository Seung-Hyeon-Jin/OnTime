import 'package:flutter/material.dart';

/// 루틴 생성 및 수정 화면에서 공통으로 사용되는 요일 선택 칩 위젯
class WeekdaySelectorWidget extends StatelessWidget {
  final List<String> selectedDays;
  final ValueChanged<List<String>> onChanged;

  static const List<Map<String, String>> allDays = [
    {'key': 'MON', 'label': '월'},
    {'key': 'TUE', 'label': '화'},
    {'key': 'WED', 'label': '수'},
    {'key': 'THU', 'label': '목'},
    {'key': 'FRI', 'label': '금'},
    {'key': 'SAT', 'label': '토'},
    {'key': 'SUN', 'label': '일'},
  ];

  const WeekdaySelectorWidget({
    super.key,
    required this.selectedDays,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    const tossBlue = Color(0xFF6C4DF6);

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: allDays.map((day) {
        final isSelected = selectedDays.contains(day['key']);
        return FilterChip(
          label: Text(
            day['label']!,
            style: TextStyle(
              color: isSelected ? Colors.white : const Color(0xFF4E5968),
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          selected: isSelected,
          selectedColor: tossBlue,
          backgroundColor: const Color(0xFFF2F4F6),
          checkmarkColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          onSelected: (selected) {
            final updated = List<String>.from(selectedDays);
            if (selected) {
              updated.add(day['key']!);
            } else {
              updated.remove(day['key']);
            }
            onChanged(updated);
          },
        );
      }).toList(),
    );
  }
}
