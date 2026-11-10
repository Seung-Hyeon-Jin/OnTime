import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter/material.dart';
import '../core/network/api_client.dart';
import '../models/location_search_model.dart';
import '../models/route_model.dart';
import '../providers/route_search_provider.dart';
import '../providers/routine_provider.dart';
import '../widgets/route_segment_widget.dart';
import 'location_search_screen.dart';

class RoutineAddScreen extends StatefulWidget {
  final VoidCallback? onRoutineAdded;

  const RoutineAddScreen({super.key, this.onRoutineAdded});

  @override
  State<RoutineAddScreen> createState() => _RoutineAddScreenState();
}

class _RoutineAddScreenState extends State<RoutineAddScreen> {
  final _formKey = GlobalKey<FormState>();

  final _routineNameController = TextEditingController();
  final _originNameController = TextEditingController();
  final _originLatController = TextEditingController();
  final _originLngController = TextEditingController();
  final _originCityCodeController = TextEditingController();

  final _destNameController = TextEditingController();
  final _destLatController = TextEditingController();
  final _destLngController = TextEditingController();
  final _destCityCodeController = TextEditingController();

  TimeOfDay _departureTime = const TimeOfDay(hour: 8, minute: 30);
  int _notifyMinsBefore = 10;
  bool _excludeHolidays = false;
  final List<String> _selectedDays = ['MON', 'TUE', 'WED', 'THU', 'FRI'];
  int _selectedRouteIndex = 0;

  // 카카오 장소 검색 전용 스크린 연결 (검색창 + 실시간 후보군 리스트)
  Future<void> _selectLocationWithKakaoSearch(bool isOrigin) async {
    final result = await Navigator.push<LocationSearchResultItemModel>(
      context,
      MaterialPageRoute(
        builder: (ctx) => LocationSearchScreen(
          title: isOrigin ? '출발지 장소/주소 검색' : '도착지 장소/주소 검색',
        ),
      ),
    );

    if (result != null) {
      setState(() {
        if (isOrigin) {
          _originNameController.text = result.placeName;
          _originLatController.text = result.latitude.toString();
          _originLngController.text = result.longitude.toString();
        } else {
          _destNameController.text = result.placeName;
          _destLatController.text = result.latitude.toString();
          _destLngController.text = result.longitude.toString();
        }
      });
    }
  }

  // 내 위치 감지하기 (스마트폰 / 브라우저 디바이스 실시간 GPS 센서 및 Reverse Geocoding)
  Future<void> _setMyCurrentLocation() async {
    setState(() {
      _originNameController.text = '📍 내 현재 위치를 감지하는 중...';
    });

    try {
      double? lat;
      double? lng;

      // 브라우저 및 기기 GPS 센서로 실제 현재 위치 위도/경도 감지
      if (kIsWeb) {
        LocationPermission permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied ||
            permission == LocationPermission.deniedForever) {
          return;
        }

        Position position = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
        );

        lat = position.latitude;
        lng = position.longitude;
      }

      if (lat == null || lng == null) {
        throw Exception('현재 디바이스의 GPS 위치를 감지할 수 없습니다.');
      }

      // 백엔드 카카오 Reverse Geocoding을 호출하여 실시간 도로명 주소 변환
      final api = ApiClient();
      final res = await api.get(
        '/api/v1/locations/reverse-geocode',
        queryParams: {'lat': lat, 'lng': lng},
      );

      final String addr = res['address_name'] ?? '내 현재 위치';

      setState(() {
        _originNameController.text = '📍 $addr';
        _originLatController.text = lat.toString();
        _originLngController.text = lng.toString();
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('현재 디바이스 위치 감지 완료: $addr'),
            behavior: SnackBarBehavior.floating,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    } catch (_) {
      setState(() {
        _originNameController.clear();
        _originLatController.clear();
        _originLngController.clear();
        _originCityCodeController.clear();
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('현재 위치 감지에 실패했습니다. 카카오 장소 검색으로 출발지를 선택해 주세요.'),
            backgroundColor: const Color(0xFFF04438),
            behavior: SnackBarBehavior.floating,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
      }
    }
  }

  // 출발지와 도착지 서로 바꾸기 (Swap)
  void _swapOriginAndDestination() {
    setState(() {
      final tempName = _originNameController.text;
      final tempLat = _originLatController.text;
      final tempLng = _originLngController.text;
      final tempCity = _originCityCodeController.text;

      _originNameController.text = _destNameController.text;
      _originLatController.text = _destLatController.text;
      _originLngController.text = _destLngController.text;
      _originCityCodeController.text = _destCityCodeController.text;

      _destNameController.text = tempName;
      _destLatController.text = tempLat;
      _destLngController.text = tempLng;
      _destCityCodeController.text = tempCity;
    });
  }

  final List<Map<String, String>> _allDays = [
    {'key': 'MON', 'label': '월'},
    {'key': 'TUE', 'label': '화'},
    {'key': 'WED', 'label': '수'},
    {'key': 'THU', 'label': '목'},
    {'key': 'FRI', 'label': '금'},
    {'key': 'SAT', 'label': '토'},
    {'key': 'SUN', 'label': '일'},
  ];

  Future<void> _handleSearchRoute() async {
    if (!_formKey.currentState!.validate()) return;

    final originName = _originNameController.text.trim();
    final originLat = double.tryParse(_originLatController.text.trim());
    final originLng = double.tryParse(_originLngController.text.trim());

    if (originName.isEmpty || originLat == null || originLng == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('출발지가 선택되지 않았습니다. 장소 검색으로 출발지를 선택해 주세요.'),
          backgroundColor: Color(0xFFF04438),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final destName = _destNameController.text.trim();
    final destLat = double.tryParse(_destLatController.text.trim());
    final destLng = double.tryParse(_destLngController.text.trim());

    if (destName.isEmpty || destLat == null || destLng == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('도착지가 선택되지 않았습니다. 장소 검색으로 도착지를 선택해 주세요.'),
          backgroundColor: Color(0xFFF04438),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final origin = LocationModel(
      name: originName,
      latitude: originLat,
      longitude: originLng,
      cityCode: _originCityCodeController.text.trim().isNotEmpty
          ? _originCityCodeController.text.trim()
          : null,
    );

    final dest = LocationModel(
      name: destName,
      latitude: destLat,
      longitude: destLng,
      cityCode: _destCityCodeController.text.trim().isNotEmpty
          ? _destCityCodeController.text.trim()
          : null,
    );

    final routeProvider =
        Provider.of<RouteSearchProvider>(context, listen: false);
    try {
      setState(() => _selectedRouteIndex = 0);
      await routeProvider.searchRoutes(origin: origin, destination: dest);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('경로 검색 실패: $e'),
            backgroundColor: const Color(0xFFF04438),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Future<void> _handleSaveRoutine() async {
    final routineProvider =
        Provider.of<RoutineProvider>(context, listen: false);

    if (_selectedDays.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('최소 하나 이상의 요일을 선택해주세요.')),
      );
      return;
    }

    final originLat = double.tryParse(_originLatController.text.trim());
    final originLng = double.tryParse(_originLngController.text.trim());
    final destLat = double.tryParse(_destLatController.text.trim());
    final destLng = double.tryParse(_destLngController.text.trim());

    if (originLat == null || originLng == null || destLat == null || destLng == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('출발지 또는 도착지 정보가 비어있습니다. 장소 검색으로 출발지와 도착지를 선택해 주세요.'),
          backgroundColor: Color(0xFFF04438),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    final formattedTime =
        '${_departureTime.hour.toString().padLeft(2, '0')}:${_departureTime.minute.toString().padLeft(2, '0')}:00';

    final origin = LocationModel(
      name: _originNameController.text.trim(),
      latitude: originLat,
      longitude: originLng,
      cityCode: _originCityCodeController.text.trim().isNotEmpty
          ? _originCityCodeController.text.trim()
          : null,
    );

    final dest = LocationModel(
      name: _destNameController.text.trim(),
      latitude: destLat,
      longitude: destLng,
      cityCode: _destCityCodeController.text.trim().isNotEmpty
          ? _destCityCodeController.text.trim()
          : null,
    );

    final routineName = _routineNameController.text.trim().isNotEmpty
        ? _routineNameController.text.trim()
        : '${_originNameController.text} ➔ ${_destNameController.text}';

    // 루틴 이름 중복 검증
    final isDuplicate = routineProvider.routines.any(
      (r) => r.name.trim().toLowerCase() == routineName.toLowerCase(),
    );

    if (isDuplicate) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('\'$routineName\' 은(는) 이미 존재하는 루틴 이름입니다.'),
          backgroundColor: const Color(0xFFF04438),
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
      return;
    }

    try {
      await routineProvider.createRoutine(
        name: routineName,
        departureStop: _originNameController.text.trim(),
        arrivalStop: _destNameController.text.trim(),
        scheduledDays: _selectedDays,
        departureTime: formattedTime,
        notifyMinsBefore: _notifyMinsBefore,
        excludeHolidays: _excludeHolidays,
        origin: origin.toJson(),
        destination: dest.toJson(),
        selectedRouteIndex: _selectedRouteIndex,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('새 출퇴근/통학 루틴이 성공적으로 등록되었습니다!'),
            behavior: SnackBarBehavior.floating,
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        );
        Provider.of<RouteSearchProvider>(context, listen: false).clearSearch();
        widget.onRoutineAdded?.call(); // 홈 탭으로 자동 이동!
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('루틴 생성 실패: $e'),
            backgroundColor: const Color(0xFFF04438),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final routeSearchProvider = Provider.of<RouteSearchProvider>(context);
    final searchResult = routeSearchProvider.searchResult;

    const tossBlue = Color(0xFF6C4DF6);
    const tossDarkText = Color(0xFF191F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF7F5FF),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                '어디로 이동하시나요?',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: tossDarkText,
                ),
              ),
              const SizedBox(height: 20),

              // Routine Info Toss Card
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
                      '루틴 정보',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: tossDarkText,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _routineNameController,
                      decoration: const InputDecoration(
                        labelText: '루틴 이름',
                        hintText: '루틴 이름을 입력해주세요',
                      ),
                      validator: (v) => v!.isEmpty ? '루틴 이름을 입력해주세요' : null,
                    ),
                    const SizedBox(height: 18),

                    // Origin Input Section
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          '출발지',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF4E5968),
                          ),
                        ),
                        TextButton.icon(
                          onPressed: _setMyCurrentLocation,
                          icon: const Icon(Icons.my_location_rounded,
                              size: 15, color: tossBlue),
                          label: const Text(
                            '📍 내 위치',
                            style: TextStyle(
                              color: tossBlue,
                              fontWeight: FontWeight.bold,
                              fontSize: 12,
                            ),
                          ),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 4),
                            backgroundColor: const Color(0xFFE8F3FF),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _originNameController,
                      readOnly: true,
                      onTap: () => _selectLocationWithKakaoSearch(true),
                      decoration: InputDecoration(
                        hintText: '출발지를 입력해주세요',
                        suffixIcon: IconButton(
                          icon:
                              const Icon(Icons.search_rounded, color: tossBlue),
                          onPressed: () => _selectLocationWithKakaoSearch(true),
                        ),
                      ),
                      validator: (v) => v!.isEmpty ? '출발지를 입력해주세요' : null,
                    ),

                    // Swap Button (출발지 ↔ 도착지 위치 전환)
                    Center(
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 12.0),
                        child: OutlinedButton.icon(
                          onPressed: _swapOriginAndDestination,
                          icon: const Icon(Icons.swap_vert_rounded,
                              size: 18, color: tossBlue),
                          label: const Text(
                            '출발지 ↔ 도착지 위치 전환',
                            style: TextStyle(
                              color: tossBlue,
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          style: OutlinedButton.styleFrom(
                            side: const BorderSide(color: Color(0xFFE8F3FF)),
                            backgroundColor: const Color(0xFFE8F3FF),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                            padding: const EdgeInsets.symmetric(
                                horizontal: 12, vertical: 6),
                          ),
                        ),
                      ),
                    ),

                    // Destination Input Section
                    const Text(
                      '도착지',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF4E5968),
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _destNameController,
                      readOnly: true,
                      onTap: () => _selectLocationWithKakaoSearch(false),
                      decoration: InputDecoration(
                        hintText: '도착지를 입력해주세요',
                        suffixIcon: IconButton(
                          icon: const Icon(Icons.search_rounded,
                              color: Color(0xFF31B057)),
                          onPressed: () =>
                              _selectLocationWithKakaoSearch(false),
                        ),
                      ),
                      validator: (v) => v!.isEmpty ? '도착지를 입력해주세요' : null,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // Search Button ("루틴 검색")
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: routeSearchProvider.isSearching
                      ? null
                      : _handleSearchRoute,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      routeSearchProvider.isSearching
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(
                                  strokeWidth: 2, color: Colors.white),
                            )
                          : const Icon(Icons.search_rounded),
                      const SizedBox(width: 8),
                      Text(routeSearchProvider.isSearching
                          ? '백엔드 경로 계산 중...'
                          : '루틴 검색'),
                    ],
                  ),
                ),
              ),

              // Search Result Toss Card with Alternative Routes Tabs
              if (searchResult != null) ...[
                const SizedBox(height: 20),
                Builder(builder: (context) {
                  final allRoutes = [searchResult, ...searchResult.alternatives]
                    ..sort((a, b) {
                      final durationCompare = a.totalDurationMinutes
                          .compareTo(b.totalDurationMinutes);
                      if (durationCompare != 0) return durationCompare;
                      return a.transferCount.compareTo(b.transferCount);
                    });
                  final selectedRoute = allRoutes[
                      _selectedRouteIndex < allRoutes.length
                          ? _selectedRouteIndex
                          : 0];

                  return Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(24),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '경로 선택 및 비교',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: tossDarkText,
                          ),
                        ),
                        const SizedBox(height: 10),

                        // Alternative Routes ChoiceChip Selector
                        SingleChildScrollView(
                          scrollDirection: Axis.horizontal,
                          child: Row(
                            children: List.generate(allRoutes.length, (idx) {
                              final route = allRoutes[idx];
                              final isSelected = _selectedRouteIndex == idx;
                              final label = idx == 0
                                  ? '✨ 추천 경로 (${route.totalDurationMinutes}분)'
                                  : '대안 경로 ${idx + 1} (${route.totalDurationMinutes}분)';
                              return Padding(
                                padding: const EdgeInsets.only(right: 8.0),
                                child: ChoiceChip(
                                  label: Text(label),
                                  selected: isSelected,
                                  onSelected: (sel) {
                                    if (sel) {
                                      setState(() => _selectedRouteIndex = idx);
                                    }
                                  },
                                  selectedColor: tossBlue,
                                  backgroundColor: const Color(0xFFF2F4F6),
                                  side: BorderSide.none,
                                  labelStyle: TextStyle(
                                    fontSize: 12,
                                    fontWeight: FontWeight.bold,
                                    color: isSelected
                                        ? Colors.white
                                        : const Color(0xFF4E5968),
                                  ),
                                ),
                              );
                            }),
                          ),
                        ),
                        const SizedBox(height: 16),

                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                '${_originNameController.text} ➔ ${_destNameController.text}',
                                style: const TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.bold,
                                  color: tossDarkText,
                                ),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFFE8F3FF),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                selectedRoute.provider,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: tossBlue,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Chip(
                              avatar: const Icon(Icons.timer_outlined,
                                  size: 16, color: tossBlue),
                              label: Text(
                                  '총 ${selectedRoute.totalDurationMinutes}분 소요'),
                              backgroundColor: const Color(0xFFF2F4F6),
                              side: BorderSide.none,
                            ),
                            const SizedBox(width: 8),
                            Chip(
                              avatar: const Icon(Icons.alt_route,
                                  size: 16, color: Color(0xFF31B057)),
                              label: Text('환승 ${selectedRoute.transferCount}회'),
                              backgroundColor: const Color(0xFFE5F9ED),
                              side: BorderSide.none,
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          '이동 경로 상세:',
                          style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: tossDarkText),
                        ),
                        const SizedBox(height: 12),
                        ...List.generate(selectedRoute.segments.length, (i) {
                          return RouteSegmentWidget(
                            segment: selectedRoute.segments[i],
                            isLast: i == selectedRoute.segments.length - 1,
                          );
                        }),
                      ],
                    ),
                  );
                }),
                const SizedBox(height: 20),

                // Time & Days Config Toss Card
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
                        '반복 요일 및 시각',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                          color: tossDarkText,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Material(
                        color: Colors.transparent,
                        child: ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text('출발 시각 설정'),
                          subtitle: Text(
                            '${_departureTime.hour.toString().padLeft(2, '0')}:${_departureTime.minute.toString().padLeft(2, '0')}',
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                              color: tossBlue,
                            ),
                          ),
                          trailing: Container(
                            padding: const EdgeInsets.all(10),
                            decoration: const BoxDecoration(
                              color: Color(0xFFF2F4F6),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.access_time_rounded,
                                color: Color(0xFF4E5968)),
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
                      const SizedBox(height: 12),
                      const Text(
                        '반복 요일 선택',
                        style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF4E5968)),
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
                      const Divider(color: Color(0xFFF2F4F6), height: 24),
                      const Text(
                        '🔔 출발 정시 미리 알림 설정',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF4E5968),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: [5, 10, 15, 20, 30].map((mins) {
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
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text(
                          '공휴일엔 알림 받지 않기',
                          style: TextStyle(
                            fontSize: 14,
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
                    ],
                  ),
                ),
                const SizedBox(height: 20),

                // Save Button
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _handleSaveRoutine,
                    child: const Text('이 경로로 루틴 저장하기'),
                  ),
                ),
              ],
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }
}
