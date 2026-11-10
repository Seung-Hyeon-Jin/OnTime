import 'package:flutter/material.dart';
import '../models/arrival_model.dart';

class ArrivalItemCard extends StatelessWidget {
  final ArrivalItem item;

  const ArrivalItemCard({super.key, required this.item});

  Color get _transportColor {
    switch (item.transportType.toUpperCase()) {
      case 'SUBWAY':
        return const Color(0xFFF59E0B); // Amber
      case 'BUS':
        return const Color(0xFF6C4DF6);
      default:
        return const Color(0xFF31B057); // Green
    }
  }

  IconData get _transportIcon {
    switch (item.transportType.toUpperCase()) {
      case 'SUBWAY':
        return Icons.directions_subway_rounded;
      case 'BUS':
        return Icons.directions_bus_rounded;
      default:
        return Icons.commute_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _transportColor.withOpacity(0.12),
              shape: BoxShape.circle,
            ),
            child: Icon(_transportIcon, color: _transportColor, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    if (item.lineName != null) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: _transportColor,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          item.lineName!,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],
                    Expanded(
                      child: Text(
                        item.stationOrStopName,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                          color: Color(0xFF191F28),
                        ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                if (item.direction != null && item.direction!.isNotEmpty)
                  Text(
                    '방향: ${item.direction}',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF8B95A1),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: const Color(0xFFE5F9ED),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              item.formattedArrival,
              style: const TextStyle(
                color: Color(0xFF31B057),
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
