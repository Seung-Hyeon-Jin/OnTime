import 'package:flutter/material.dart';
import '../models/route_model.dart';

class RouteSegmentWidget extends StatelessWidget {
  final RouteSegmentModel segment;
  final bool isLast;

  const RouteSegmentWidget({
    super.key,
    required this.segment,
    this.isLast = false,
  });

  Color _getBadgeColor(String type) {
    switch (type.toUpperCase()) {
      case 'BUS':
        return const Color(0xFF6C4DF6);
      case 'SUBWAY':
        return const Color(0xFFF59E0B); // Amber/Yellow
      case 'WALK':
        return const Color(0xFF8B95A1); // Grey
      default:
        return const Color(0xFF31B057); // Green
    }
  }

  IconData _getIcon(String type) {
    switch (type.toUpperCase()) {
      case 'BUS':
        return Icons.directions_bus_rounded;
      case 'SUBWAY':
        return Icons.directions_subway_rounded;
      case 'WALK':
        return Icons.directions_walk_rounded;
      default:
        return Icons.commute_rounded;
    }
  }

  @override
  Widget build(BuildContext context) {
    final badgeColor = _getBadgeColor(segment.transportType);

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: badgeColor.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: Icon(
                _getIcon(segment.transportType),
                color: badgeColor,
                size: 18,
              ),
            ),
            if (!isLast)
              Container(
                width: 2,
                height: 36,
                color: const Color(0xFFE5E8EB),
              ),
          ],
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Flexible(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: badgeColor,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        segment.transportType == 'WALK'
                            ? '도보'
                            : segment.lineName ?? segment.transportType,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Flexible(
                    child: Text(
                      '${segment.durationMinutes}분 소요',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Color(0xFF191F28),
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              if (segment.departureStop != null && segment.arrivalStop != null)
                Text(
                  '${segment.departureStop} ➔ ${segment.arrivalStop}',
                  softWrap: true,
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF4E5968),
                  ),
                ),
              if (segment.stops.isNotEmpty) ...[
                const SizedBox(height: 2),
                Text(
                  '${segment.stops.length}개 정류장 이동',
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF8B95A1),
                  ),
                ),
              ],
              const SizedBox(height: 12),
            ],
          ),
        ),
      ],
    );
  }
}
