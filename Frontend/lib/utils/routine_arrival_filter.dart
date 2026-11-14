import '../models/arrival_model.dart';
import '../models/route_model.dart';
import '../models/routine_model.dart';

/// 실시간 버스 및 지하철 도착 정보 정규화 & 매칭 유틸리티
class RoutineArrivalFilter {
  RoutineArrivalFilter._();

  static String normalizeLine(String value) {
    var cleaned =
        value.replaceAll(RegExp(r'\s+'), '').replaceAll('번', '').trim();
    const prefixes = [
      '마을',
      '일반',
      '지선',
      '간선',
      '직행',
      '좌석',
      '광역',
      '시내',
      '농어촌',
      '급행',
      '순환',
      '맞춤'
    ];
    for (final prefix in prefixes) {
      if (cleaned.startsWith(prefix)) {
        cleaned = cleaned.substring(prefix.length);
      }
    }
    return cleaned.trim();
  }

  static String getBaseLineNumber(String lineName) {
    final normalized = normalizeLine(lineName);
    final match = RegExp(r'^([A-Za-z]*\d+)').firstMatch(normalized);
    if (match != null) {
      return match.group(1)!;
    }
    return normalized;
  }

  static String? normalizeStopName(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    var compact = value.replaceAll(RegExp(r'\s+'), '');
    if (compact.endsWith('역')) {
      compact = compact.substring(0, compact.length - 1);
    }
    return compact;
  }

  static bool isSameStop(String? left, String? right) {
    if (left == null || right == null) return false;
    return left.contains(right) || right.contains(left);
  }

  static String? getFirstBusLine(RouteResponseModel? route) {
    if (route == null) return null;
    for (final seg in route.segments) {
      if (seg.transportType == 'BUS' &&
          seg.lineName != null &&
          seg.lineName!.isNotEmpty) {
        return seg.lineName;
      }
    }
    return null;
  }

  static String? getFirstBusArrivalName(RouteResponseModel route) {
    for (final seg in route.segments) {
      if (seg.transportType == 'BUS') {
        if (seg.arrivalStop != null && seg.arrivalStop!.trim().isNotEmpty) {
          return normalizeStopName(seg.arrivalStop);
        }
        if (seg.stops.isNotEmpty) {
          return normalizeStopName(seg.stops.last.name);
        }
        return null;
      }
    }
    return null;
  }

  static String? getFirstBusDepartureName(RouteResponseModel route) {
    for (final segment in route.segments) {
      if (segment.transportType != 'BUS') continue;
      if (segment.departureStop != null &&
          segment.departureStop!.trim().isNotEmpty) {
        return normalizeStopName(segment.departureStop);
      }
      if (segment.stops.isNotEmpty) {
        return normalizeStopName(segment.stops.first.name);
      }
      return null;
    }
    return null;
  }

  static List<String> getSameDestinationBusLines(RoutineModel routine) {
    final List<String> candidateLines = [];
    final routePlan = routine.routePlan?.route;
    if (routePlan == null) return candidateLines;

    final targetArrival = getFirstBusArrivalName(routePlan) ??
        normalizeStopName(routine.arrivalStop);
    final primaryDeparture = getFirstBusDepartureName(routePlan);
    final primaryLine = getFirstBusLine(routePlan);
    if (primaryLine != null) {
      candidateLines.add(primaryLine);
    }

    final allRoutes = [routePlan, ...routePlan.alternatives];
    for (final route in allRoutes) {
      final line = getFirstBusLine(route);
      final arrival = getFirstBusArrivalName(route);
      final departure = getFirstBusDepartureName(route);
      if (line == null) continue;

      if (arrival != null &&
          targetArrival != null &&
          !isSameStop(arrival, targetArrival)) {
        continue;
      }
      if (departure == null ||
          primaryDeparture == null ||
          !isSameStop(departure, primaryDeparture)) {
        continue;
      }
      if (!candidateLines.contains(line)) {
        candidateLines.add(line);
      }
    }

    return candidateLines;
  }

  static List<ArrivalItem> extractFirstLegArrivals(RoutineExecutionModel execution) {
    final arrivals = <ArrivalItem>[];
    for (final segment in execution.route.segments) {
      if (segment.transportType == 'BUS' || segment.transportType == 'SUBWAY') {
        for (final stop in segment.stops) {
          arrivals.addAll(stop.arrivals);
        }
        break;
      }
    }
    return arrivals;
  }

  static List<ArrivalItem> deduplicateArrivals(List<ArrivalItem> arrivals) {
    final seen = <String>{};
    return arrivals.where((arrival) {
      final line = normalizeLine(arrival.lineName ?? '');
      final vehicle = (arrival.vehicleNumber ?? '').trim();
      final seconds = arrival.arrivalSeconds ?? -1;
      final msg = (arrival.arrivalMessage ?? '').trim();

      final key = vehicle.isNotEmpty
          ? '${arrival.transportType.toUpperCase()}|$line|$vehicle'
          : '${arrival.transportType.toUpperCase()}|$line|$seconds|$msg';

      return seen.add(key);
    }).toList();
  }

  static bool isMatchingBusLine(String lineName, List<String> allowedLines) {
    final normLine = normalizeLine(lineName);
    final normAllowed = allowedLines.map(normalizeLine).toSet();

    if (normAllowed.contains(normLine)) return true;

    final baseLine = getBaseLineNumber(normLine);
    for (final allowed in normAllowed) {
      if (getBaseLineNumber(allowed) == baseLine) {
        return true;
      }
    }
    return false;
  }

  static int compareArrivals(ArrivalItem a, ArrivalItem b) {
    if (a.arrivalSeconds != null && b.arrivalSeconds != null) {
      return a.arrivalSeconds!.compareTo(b.arrivalSeconds!);
    }
    if (a.arrivalSeconds != null) return -1;
    if (a.arrivalSeconds == null && b.arrivalSeconds != null) return 1;
    return 0;
  }
}
