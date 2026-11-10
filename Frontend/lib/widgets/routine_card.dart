import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../models/arrival_model.dart';
import '../models/routine_model.dart';
import '../models/route_model.dart';
import '../providers/routine_provider.dart';
import '../screens/routine_edit_screen.dart';
import 'route_segment_widget.dart';

class RoutineCard extends StatefulWidget {
  final RoutineModel routine;

  const RoutineCard({super.key, required this.routine});

  @override
  State<RoutineCard> createState() => _RoutineCardState();
}

class _RoutineCardState extends State<RoutineCard> {
  bool _isRefreshing = false;
  bool _isExpanded = false;
  Timer? _countdownTimer;
  DateTime? _lastRefreshedAt;

  int get _remainingCooldownSeconds {
    if (_lastRefreshedAt == null) return 0;
    final elapsed = DateTime.now().difference(_lastRefreshedAt!).inSeconds;
    final remaining = 30 - elapsed;
    return remaining > 0 ? remaining : 0;
  }

  @override
  void initState() {
    super.initState();
    // 디바이스 온디바이스 1초 주기 실시간 카운트다운 타이머
    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (mounted) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    super.dispose();
  }

  String _formatLiveRemainingTime(
      ArrivalItem arrival, RoutineExecutionModel? execution) {
    if (arrival.arrivalSeconds == null || arrival.arrivalSeconds! <= 0) {
      return arrival.formattedArrival;
    }

    if (execution == null || execution.lastCheckedAt.isEmpty) {
      return arrival.formattedArrival;
    }

    try {
      final checkedAt = DateTime.parse(execution.lastCheckedAt).toLocal();
      final elapsed = DateTime.now().difference(checkedAt).inSeconds;
      final currentRemaining = arrival.arrivalSeconds! - elapsed;

      if (currentRemaining <= 0) {
        return '곧 도착';
      }

      final mins = currentRemaining ~/ 60;
      final secs = currentRemaining % 60;
      if (mins == 0) {
        return '$secs초 후 도착';
      }
      if (secs == 0) {
        return '$mins분 후 도착';
      }
      return '$mins분 $secs초 후 도착';
    } catch (_) {
      return arrival.formattedArrival;
    }
  }

  void _showToast(String message, {Color? backgroundColor}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: backgroundColor,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  Future<void> _handleRefreshExecution() async {
    final cooldown = _remainingCooldownSeconds;
    if (cooldown > 0) {
      _showToast('30초 마다 조회가 가능합니다. ($cooldown초 후 가능)');
      return;
    }

    setState(() {
      _isRefreshing = true;
      _lastRefreshedAt = DateTime.now();
    });
    try {
      await Provider.of<RoutineProvider>(context, listen: false)
          .executeRoutine(widget.routine.routineId);
      _showToast('실시간 대중교통 정보가 성공적으로 갱신되었습니다.');
    } catch (e) {
      _showToast('실시간 정보 갱신 실패: $e', backgroundColor: const Color(0xFFF04438));
    } finally {
      if (mounted) {
        setState(() => _isRefreshing = false);
      }
    }
  }

  String? _getFirstTransitType(RouteResponseModel? route) {
    if (route == null) return null;
    for (final segment in route.segments) {
      if (segment.transportType == 'BUS' || segment.transportType == 'SUBWAY') {
        return segment.transportType;
      }
    }
    return null;
  }

  // 등록된 루틴의 메인 지정 버스 노선 번호 추출 (e.g. 3001번, 1번, 720-3번)
  String? _getRoutineFirstBusLine() {
    final route = widget.routine.routePlan?.route;
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

  String? _normalizeStopName(String? value) {
    if (value == null || value.trim().isEmpty) return null;
    var compact = value.replaceAll(RegExp(r'\s+'), '');
    if (compact.endsWith('역')) {
      compact = compact.substring(0, compact.length - 1);
    }
    return compact;
  }

  bool _isSameStop(String? left, String? right) {
    if (left == null || right == null) return false;
    return left.contains(right) || right.contains(left);
  }

  String? _firstBusArrivalName(RouteResponseModel route) {
    for (final seg in route.segments) {
      if (seg.transportType == 'BUS') {
        if (seg.arrivalStop != null && seg.arrivalStop!.trim().isNotEmpty) {
          return _normalizeStopName(seg.arrivalStop);
        }
        if (seg.stops.isNotEmpty) {
          return _normalizeStopName(seg.stops.last.name);
        }
        return null;
      }
    }
    return null;
  }

  String? _firstBusLine(RouteResponseModel route) {
    for (final seg in route.segments) {
      if (seg.transportType == 'BUS' &&
          seg.lineName != null &&
          seg.lineName!.trim().isNotEmpty) {
        return seg.lineName!.trim();
      }
    }
    return null;
  }

  String? _firstBusDepartureName(RouteResponseModel route) {
    for (final segment in route.segments) {
      if (segment.transportType != 'BUS') continue;
      if (segment.departureStop != null &&
          segment.departureStop!.trim().isNotEmpty) {
        return _normalizeStopName(segment.departureStop);
      }
      if (segment.stops.isNotEmpty) {
        return _normalizeStopName(segment.stops.first.name);
      }
      return null;
    }

    return null;
  }

  bool _hasSameBusEndpoints(
      RouteResponseModel primary, RouteResponseModel alternative) {
    final primaryDeparture = _firstBusDepartureName(primary);
    final alternativeDeparture = _firstBusDepartureName(alternative);
    return primaryDeparture != null &&
        alternativeDeparture != null &&
        _isSameStop(primaryDeparture, alternativeDeparture);
  }

  // 등록 경로와 같은 하차 지점으로 가는 검증된 직통 노선만 후보로 둡니다.
  List<String> _getSameDestinationBusLines() {
    final List<String> candidateLines = [];
    final routePlan = widget.routine.routePlan?.route;
    if (routePlan == null) return candidateLines;

    final targetArrival = _firstBusArrivalName(routePlan) ??
        _normalizeStopName(widget.routine.arrivalStop);
    final primaryDeparture = _firstBusDepartureName(routePlan);
    final primaryLine = _firstBusLine(routePlan);
    if (primaryLine != null) {
      candidateLines.add(primaryLine);
    }

    // 메인 경로와 대안 경로에서 동일 하차 정류장으로 가는 노선을 수집합니다.
    final allRoutes = [routePlan, ...routePlan.alternatives];
    for (final route in allRoutes) {
      final line = _firstBusLine(route);
      final arrival = _firstBusArrivalName(route);
      final departure = _firstBusDepartureName(route);
      if (line == null) continue;

      if (arrival != null &&
          targetArrival != null &&
          !_isSameStop(arrival, targetArrival)) {
        continue;
      }
      if (departure == null ||
          primaryDeparture == null ||
          !_isSameStop(departure, primaryDeparture)) {
        continue;
      }
      if (!candidateLines.contains(line)) {
        candidateLines.add(line);
      }
    }

    return candidateLines;
  }

  // 실시간 도착 정보 추출: 메인 경로의 첫 번째 대중교통(버스/지하철) 구간 정류장에서만 수집합니다.
  List<ArrivalItem> _extractFirstLegArrivals(RoutineExecutionModel execution) {
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

  List<ArrivalItem> _deduplicateArrivals(List<ArrivalItem> arrivals) {
    final seen = <String>{};
    return arrivals.where((arrival) {
      final line = _normalizeLine(arrival.lineName ?? '');
      final vehicle = (arrival.vehicleNumber ?? '').trim();
      final seconds = arrival.arrivalSeconds ?? -1;
      final msg = (arrival.arrivalMessage ?? '').trim();

      // 차량 번호가 있으면 (교통수단 | 노선명 | 차량번호), 없으면 (교통수단 | 노선명 | 잔여초 | 메시지)로 엄격히 중복 제거
      final key = vehicle.isNotEmpty
          ? '${arrival.transportType.toUpperCase()}|$line|$vehicle'
          : '${arrival.transportType.toUpperCase()}|$line|$seconds|$msg';

      return seen.add(key);
    }).toList();
  }

  String? _extractFirstLegArrivalError(RoutineExecutionModel execution) {
    for (final segment in execution.route.segments) {
      if (segment.transportType == 'BUS' || segment.transportType == 'SUBWAY') {
        for (final stop in segment.stops) {
          if (stop.arrivalError != null && stop.arrivalError!.isNotEmpty) {
            final error = stop.arrivalError!;
            if (error.contains('운행종료') || error.contains('운행 종료')) {
              return '도착정보없음';
            }
            return error;
          }
        }
      }
    }
    return null;
  }

  bool _isCardinalSubwayDirection(String value) {
    const cardinal = {'상행', '하행', '내선', '외선'};
    return cardinal.contains(value.replaceAll(' ', ''));
  }

  bool _matchesSubwayDirection(ArrivalItem arrival, String? destination) {
    if (destination == null || destination.isEmpty) return true;
    final direction = arrival.direction;
    if (direction == null || direction.isEmpty) return true;
    if (_isCardinalSubwayDirection(direction)) return true;
    final normalizedDirection =
        _normalizeStopName(direction) ?? direction.replaceAll(' ', '');
    return normalizedDirection.contains(destination);
  }

  // 루틴의 첫 지하철 구간 도착역명을 방면 표시에 사용합니다.
  String? _getSubwayDirection() {
    final route = widget.routine.routePlan?.route;
    if (route == null) return null;
    for (final seg in route.segments) {
      if (seg.transportType == 'SUBWAY') {
        // 종착역(마지막 정류장)을 방면 기준으로 사용합니다.
        // 종착역 방면이 목적지와 일치하는지 확인합니다.
        if (seg.stops.isNotEmpty) {
          return _normalizeStopName(seg.stops.last.name);
        }
        if (seg.arrivalStop != null && seg.arrivalStop!.isNotEmpty) {
          return _normalizeStopName(seg.arrivalStop);
        }
      }
    }
    return null;
  }

  String _normalizeLine(String value) {
    var cleaned =
        value.replaceAll(RegExp(r'\s+'), '').replaceAll('번', '').trim();
    final prefixes = [
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

  Widget _buildDetailedRouteColumn(
      RouteResponseModel route, String label, Color labelColor) {
    return Container(
      width: 240,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFE5E8EB)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: labelColor,
            ),
          ),
          const SizedBox(height: 8),
          ...List.generate(route.segments.length, (i) {
            return RouteSegmentWidget(
              segment: route.segments[i],
              isLast: i == route.segments.length - 1,
            );
          }),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final routineProvider = Provider.of<RoutineProvider>(context);
    final execution = routineProvider.executions[widget.routine.routineId];
    final isExpanded = _isExpanded;

    const tossBlue = Color(0xFF6C4DF6);
    const tossDarkText = Color(0xFF191F28);

    final displayRoute = execution?.route ?? widget.routine.routePlan?.route;
    final firstTransitType = _getFirstTransitType(displayRoute);
    final isSubwayRoutine = firstTransitType == 'SUBWAY';

    // 1. 내가 지정한 메인 버스 노선
    final primaryLine =
        (displayRoute == null ? null : _firstBusLine(displayRoute)) ??
            _getRoutineFirstBusLine() ??
            '';

    // 2. 루틴 등록 시 검증 저장된 동일 정류장 ➔ 동일 목적지 행 모든 버스 노선 후보군 (e.g. 1번, 3001번, 3002번)
    final sameDestBusLines = _getSameDestinationBusLines();
    final altLines =
        sameDestBusLines.where((l) => l.trim() != primaryLine.trim()).toList();

    // 3. 실시간 수신 도착 정보 추출: 첫 번째 대중교통 구간에서만 수집
    final rawFirstLegArrivals = execution != null
        ? _extractFirstLegArrivals(execution)
        : <ArrivalItem>[];

    // 타입 필터링 (BUS or SUBWAY)
    final realArrivals = _deduplicateArrivals(rawFirstLegArrivals)
        .where((a) => a.transportType.toUpperCase() == firstTransitType)
        .toList();

    // 지하철: 상행/하행만 있는 항목은 숨기지 않고, 종착역명이 있으면 목적지 방면을 우선합니다.
    final routineDirection = _getSubwayDirection();
    final matchingSubwayArrivals = isSubwayRoutine
        ? realArrivals
            .where((a) => _matchesSubwayDirection(a, routineDirection))
            .toList()
        : realArrivals;
    final filteredSubwayArrivals = matchingSubwayArrivals.isNotEmpty
        ? matchingSubwayArrivals
        : realArrivals;
    final arrivalLookupError =
        execution != null ? _extractFirstLegArrivalError(execution) : null;

    String getBaseLineNumber(String lineName) {
      final normalized = _normalizeLine(lineName);
      final match = RegExp(r'^([A-Za-z]*\d+)').firstMatch(normalized);
      if (match != null) {
        return match.group(1)!;
      }
      return normalized;
    }

    bool isMatchingBusLine(String lineName, List<String> allowedLines) {
      final normLine = _normalizeLine(lineName);
      final normAllowed = allowedLines.map(_normalizeLine).toSet();

      if (normAllowed.contains(normLine)) return true;

      final baseLine = getBaseLineNumber(normLine);
      for (final allowed in normAllowed) {
        if (getBaseLineNumber(allowed) == baseLine) {
          return true;
        }
      }
      return false;
    }

    // 1단계 교집합 필터링: 동일 목적지 검증 노선 및 파생/파생지선 버스(1-3번, 1A번 등) 수집
    final validArrivals = realArrivals.where((a) {
      if (a.lineName == null) return false;
      return isMatchingBusLine(a.lineName!, sameDestBusLines);
    }).toList();

    // 2단계 메인 지정 버스의 실시간 도착 정보 (양쪽 모두 정규화해 비교)
    final primaryArrivals = validArrivals.where((a) {
      if (a.lineName == null) return false;
      return _normalizeLine(a.lineName!) == _normalizeLine(primaryLine);
    }).toList();

    // 3단계 검증된 대체 버스의 실시간 도착 정보만 표시합니다.
    final altArrivals = validArrivals.where((a) {
      if (a.lineName == null) return false;
      return _normalizeLine(a.lineName!) != _normalizeLine(primaryLine);
    }).toList();

    // 4단계 도착 잔여시간(arrivalSeconds) 오름차순 시간순 정렬 (가장 빨리 도착하는 차량이 맨 앞으로!)
    int compareArrivals(ArrivalItem a, ArrivalItem b) {
      if (a.arrivalSeconds != null && b.arrivalSeconds != null) {
        return a.arrivalSeconds!.compareTo(b.arrivalSeconds!);
      }
      if (a.arrivalSeconds != null) return -1;
      if (b.arrivalSeconds != null) return 1;
      return 0;
    }

    primaryArrivals.sort(compareArrivals);
    altArrivals.sort(compareArrivals);
    filteredSubwayArrivals.sort(compareArrivals);

    // 등록 노선과 일치하는 버스가 없으면 실제 정보 없음으로 표시합니다.
    // 관계없는 노선(22번, 11-2번 등)을 fallback으로 보여주지 않습니다.
    final displayedPrimaryArrivals =
        primaryArrivals.isNotEmpty ? primaryArrivals : <ArrivalItem>[];
    final primaryArrivalTitle = primaryLine.isEmpty
        ? '🚌 버스 도착 정보:'
        : '🚌 지정 버스 ($primaryLine번) 도착 정보:';

    return Opacity(
      opacity: widget.routine.enabled ? 1.0 : 0.55,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(18.0),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFFFDFCFF), Color(0xFFEDE8FF)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(26),
          border: Border.all(
            color: Color(0xFFBFAFFF),
            width: 1.5,
          ),
          boxShadow: [
            BoxShadow(
              color: tossBlue.withValues(alpha: 0.16),
              blurRadius: 24,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Routine Name & Day Tag & Edit Icon
          InkWell(
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => RoutineEditScreen(routine: widget.routine),
                ),
              );
            },
            borderRadius: BorderRadius.circular(12),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Row(
                    children: [
                      Container(
                        width: 38,
                        height: 38,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xFF8067FF), Color(0xFF5C43E5)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(13),
                          boxShadow: [
                            BoxShadow(
                              color: tossBlue.withValues(alpha: 0.22),
                              blurRadius: 10,
                              offset: const Offset(0, 4),
                            ),
                          ],
                        ),
                        child: Icon(
                          isSubwayRoutine
                              ? Icons.subway_rounded
                              : Icons.directions_bus_filled_rounded,
                          color: Colors.white,
                          size: 21,
                        ),
                      ),
                      const SizedBox(width: 11),
                      Flexible(
                        child: Text(
                          widget.routine.name,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: tossDarkText,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      const SizedBox(width: 6),
                      const Icon(
                        Icons.edit_outlined,
                        size: 16,
                        color: Color(0xFF8B95A1),
                      ),
                    ],
                  ),
                ),
                Row(
                  children: [
                    if (widget.routine.excludeHolidays) ...[
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFFF3C4),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          '🏖️ 공휴일 제외',
                          style: TextStyle(
                            color: Color(0xFFB45309),
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 6),
                    ],
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 11, vertical: 6),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.72),
                        borderRadius: BorderRadius.circular(99),
                        border: Border.all(
                          color: const Color(0xFFD8CFFF),
                        ),
                      ),
                      child: Text(
                        widget.routine.daysSummary,
                        style: const TextStyle(
                          color: Color(0xFF5B43D6),
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Origin & Destination Timeline
          InkWell(
            onTap: () => setState(() => _isExpanded = !_isExpanded),
            borderRadius: BorderRadius.circular(16),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Column(
                children: [
                  Row(
                    children: [
                      Column(
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: tossBlue,
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                          Container(
                            width: 2,
                            height: 24,
                            color: const Color(0xFFE5E8EB),
                          ),
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: const Color(0xFFF04438),
                              borderRadius: BorderRadius.circular(5),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.routine.departureStop,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                color: tossDarkText,
                              ),
                            ),
                            const SizedBox(height: 12),
                            Text(
                              widget.routine.arrivalStop,
                              style: const TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w600,
                                color: tossDarkText,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          const Text(
                            '출발 정시',
                            style: TextStyle(
                              fontSize: 12,
                              color: Color(0xFF8B95A1),
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            widget.routine.formattedDepartureTime,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: tossBlue,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: const Color(0xFFE5F9ED),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                const Icon(Icons.notifications_active_rounded,
                                    size: 11, color: Color(0xFF15803D)),
                                const SizedBox(width: 4),
                                Text(
                                  '${widget.routine.notifyMinsBefore}분 전 알림',
                                  style: const TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: Color(0xFF15803D),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        isExpanded ? '상세 경로 접기' : '🗺️ 전체 상세 경로 펼쳐보기',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: tossBlue,
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(
                        isExpanded
                            ? Icons.keyboard_arrow_up_rounded
                            : Icons.keyboard_arrow_down_rounded,
                        color: tossBlue,
                        size: 18,
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Expanded Full Detailed Route Pipeline
          if (isExpanded) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF9FAFB),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE5E8EB)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    '🗺️ 전체 이동 경로 (구간별 상세):',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: tossDarkText,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (displayRoute != null && displayRoute.segments.isNotEmpty)
                    Builder(
                      builder: (context) {
                        final alternativeRoutes = firstTransitType == 'BUS' &&
                                _firstBusDepartureName(displayRoute) != null
                            ? () {
                                return displayRoute.alternatives
                                    .where((route) => _hasSameBusEndpoints(
                                        displayRoute, route))
                                    .toList();
                              }()
                            : <RouteResponseModel>[];

                        if (alternativeRoutes.isEmpty) {
                          return Column(
                            children: [
                              ...List.generate(displayRoute.segments.length,
                                  (i) {
                                return RouteSegmentWidget(
                                  segment: displayRoute.segments[i],
                                  isLast: i == displayRoute.segments.length - 1,
                                );
                              }),
                            ],
                          );
                        }

                        return SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _buildDetailedRouteColumn(
                                displayRoute,
                                '기본 경로',
                                tossBlue,
                              ),
                              ...List.generate(alternativeRoutes.length, (i) {
                                return Padding(
                                  padding: const EdgeInsets.only(left: 10),
                                  child: _buildDetailedRouteColumn(
                                    alternativeRoutes[i],
                                    '대안 버스 ${i + 1}',
                                    const Color(0xFFFF8A4C),
                                  ),
                                );
                              }),
                            ],
                          ),
                        );
                      },
                    )
                  else
                    const Text(
                      '저장된 상세 경로 정보가 없습니다.',
                      style: TextStyle(fontSize: 12, color: Color(0xFF8B95A1)),
                    ),
                ],
              ),
            ),
          ],

          // Clean Live Execution Section (사용자가 상태조회를 실행한 경우에만 도착 정보 카드 표출)
          if (execution != null) ...[
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF9FAFB),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE5E8EB)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Total Duration to Destination
                  if (displayRoute != null &&
                      displayRoute.totalDurationMinutes > 0) ...[
                    Row(
                      children: [
                        const Icon(Icons.timer_outlined,
                            size: 18, color: tossBlue),
                        const SizedBox(width: 6),
                        Text(
                          '목적지까지 약 ${displayRoute.totalDurationMinutes}분 예상',
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: tossDarkText,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                  ],

                  // Arriving Transit Vehicles
                  if (isSubwayRoutine) ...[
                    _buildTransitArrivals(
                      title:
                          '🚇 지하철 도착 정보${routineDirection != null ? ' ($routineDirection 방면)' : ''}:',
                      arrivals: filteredSubwayArrivals,
                      emptyText: arrivalLookupError ?? '도착 정보 없음',
                      execution: execution,
                      isSubway: true,
                    ),
                  ] else ...[
                    _buildTransitArrivals(
                      title: primaryArrivalTitle,
                      arrivals: displayedPrimaryArrivals,
                      emptyText: '도착 정보 없음',
                      execution: execution,
                    ),
                    if (altLines.isNotEmpty || altArrivals.isNotEmpty) ...[
                      const SizedBox(height: 10),
                      const Text(
                        '⚡ 대체 버스 도착 정보:',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF31B057),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: altArrivals.isNotEmpty
                            ? altArrivals.map((arr) {
                                return _buildBusChip(
                                  '${arr.lineName}번 버스',
                                  _formatLiveRemainingTime(arr, execution),
                                  false,
                                );
                              }).toList()
                            : altLines.map((line) {
                                return _buildBusChip(
                                  '$line번 버스',
                                  '도착 정보 없음',
                                  false,
                                );
                              }).toList(),
                      ),
                    ],
                  ],
                ],
              ),
            ),
          ],

          const SizedBox(height: 16),
          // Actions: Full Width Refresh Button
          Builder(
            builder: (context) {
              final cooldown = _remainingCooldownSeconds;
              final isButtonDisabled = _isRefreshing || cooldown > 0;

              return SizedBox(
                width: double.infinity,
                height: 42,
                child: OutlinedButton.icon(
                  onPressed: _isRefreshing
                      ? null
                      : (cooldown > 0
                          ? () {
                              ScaffoldMessenger.of(context)
                                  .hideCurrentSnackBar();
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(
                                      '30초 마다 조회가 가능합니다. ($cooldown초 후 가능)'),
                                  behavior: SnackBarBehavior.floating,
                                  shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(12)),
                                  duration: const Duration(seconds: 2),
                                ),
                              );
                            }
                          : _handleRefreshExecution),
                  icon: _isRefreshing
                      ? const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: tossBlue,
                          ),
                        )
                      : Icon(
                          Icons.refresh_rounded,
                          size: 18,
                          color: isButtonDisabled
                              ? const Color(0xFF8B95A1)
                              : tossBlue,
                        ),
                  label: Text(
                    _isRefreshing
                        ? '실시간 연동 중...'
                        : (cooldown > 0
                            ? '조회 대기 중 (${cooldown}초)'
                            : '실시간 상태 조회'),
                    style: TextStyle(
                      color:
                          isButtonDisabled ? const Color(0xFF8B95A1) : tossBlue,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                  style: OutlinedButton.styleFrom(
                    side: BorderSide(
                      color: isButtonDisabled
                          ? const Color(0xFFE5E8EB)
                          : const Color(0xFFEDE9FF),
                    ),
                    backgroundColor: isButtonDisabled
                        ? const Color(0xFFF0EDFF)
                        : const Color(0xFFEDE9FF),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ),
      ),
    );
  }

  Widget _buildTransitArrivals({
    required String title,
    required List<ArrivalItem> arrivals,
    required String emptyText,
    RoutineExecutionModel? execution,
    bool isSubway = false,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: Color(0xFF4E5968),
          ),
        ),
        const SizedBox(height: 6),
        Wrap(
          spacing: 6,
          runSpacing: 4,
          children: arrivals.isNotEmpty
              ? arrivals.map((arrival) {
                  final line = arrival.lineName ?? (isSubway ? '지하철' : '버스');
                  final direction = arrival.direction;
                  final title = isSubway
                      ? (direction != null &&
                              direction.isNotEmpty &&
                              !_isCardinalSubwayDirection(direction)
                          ? '$line · $direction'
                          : line)
                      : '$line번 버스';
                  return _buildBusChip(
                    title,
                    _formatLiveRemainingTime(arrival, execution),
                    true,
                  );
                }).toList()
              : [
                  _buildBusChip(
                    isSubway ? '지하철' : '버스',
                    emptyText,
                    true,
                  ),
                ],
        ),
      ],
    );
  }

  Widget _buildBusChip(String lineName, String arrivalText, bool isMainBus) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: isMainBus
            ? const Color(0xFF6C4DF6)
            : const Color(0xFFE5F9ED), // Main: Toss Blue, Alt: Soft Green
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            isMainBus ? Icons.directions_bus_rounded : Icons.bolt_rounded,
            size: 12,
            color: isMainBus ? Colors.white : const Color(0xFF15803D),
          ),
          const SizedBox(width: 4),
          Text(
            '$lineName ($arrivalText)',
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: isMainBus ? Colors.white : const Color(0xFF15803D),
            ),
          ),
        ],
      ),
    );
  }
}
