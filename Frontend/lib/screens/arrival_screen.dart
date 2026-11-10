import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../providers/arrival_provider.dart';
import '../widgets/arrival_item_card.dart';

class ArrivalScreen extends StatefulWidget {
  const ArrivalScreen({super.key});

  @override
  State<ArrivalScreen> createState() => _ArrivalScreenState();
}

class _ArrivalScreenState extends State<ArrivalScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  final _subwayController = TextEditingController(text: '강남');
  final _busStopNameController = TextEditingController();
  final _busCityCodeController = TextEditingController();
  final _busStationIdController = TextEditingController();
  List<Map<String, dynamic>> _busStopSuggestions = [];
  bool _isSearchingBusStops = false;
  String? _busStopSearchError;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _busStopNameController.dispose();
    _busCityCodeController.dispose();
    _busStationIdController.dispose();
    super.dispose();
  }

  void _searchSubway() {
    final query = _subwayController.text.trim();
    if (query.isNotEmpty) {
      Provider.of<ArrivalProvider>(context, listen: false)
          .getSubwayArrivals(query);
    }
  }

  void _searchBus() {
    final cityCode = _busCityCodeController.text.trim();
    final stationId = _busStationIdController.text.trim();
    if (cityCode.isEmpty || stationId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('먼저 버스 정류장을 검색하고 선택해 주세요.')),
      );
      return;
    }
    Provider.of<ArrivalProvider>(context, listen: false)
        .getBusArrivals(cityCode, stationId);
  }

  Future<void> _searchBusStops() async {
    final query = _busStopNameController.text.trim();
    if (query.isEmpty) {
      setState(() {
        _busStopSuggestions = [];
        _busStopSearchError = '정류장 이름을 입력해 주세요.';
      });
      return;
    }

    setState(() {
      _isSearchingBusStops = true;
      _busStopSearchError = null;
      _busStopSuggestions = [];
      _busCityCodeController.clear();
      _busStationIdController.clear();
    });

    try {
      final response = await ApiClient().get(
        ApiConfig.busStopsSearch,
        queryParams: {'query': query},
      );
      final items = response is Map ? response['items'] : null;
      if (!mounted) return;
      setState(() {
        _busStopSuggestions = items is List
            ? items
                .whereType<Map>()
                .map((item) => Map<String, dynamic>.from(item))
                .toList()
            : [];
        if (_busStopSuggestions.isEmpty) {
          _busStopSearchError = '검색된 정류장이 없습니다.';
        }
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _busStopSearchError = '정류장 검색에 실패했습니다: $e';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSearchingBusStops = false;
        });
      }
    }
  }

  void _selectBusStop(Map<String, dynamic> stop) {
    setState(() {
      _busStopNameController.text = stop['name']?.toString() ?? '';
      _busCityCodeController.text = stop['city_code']?.toString() ?? '';
      _busStationIdController.text = stop['station_id']?.toString() ?? '';
      _busStopSuggestions = [];
      _busStopSearchError = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final arrivalProvider = Provider.of<ArrivalProvider>(context);

    const tossBlue = Color(0xFF6C4DF6);

    return Scaffold(
      backgroundColor: const Color(0xFFF7F5FF),
      appBar: AppBar(
        title: const Text('실시간 도착'),
        backgroundColor: const Color(0xFFF7F5FF),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(14),
            ),
            child: TabBar(
              controller: _tabController,
              indicator: BoxDecoration(
                color: tossBlue,
                borderRadius: BorderRadius.circular(10),
              ),
              labelColor: Colors.white,
              unselectedLabelColor: const Color(0xFF8B95A1),
              labelStyle:
                  const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              indicatorSize: TabBarIndicatorSize.tab,
              dividerColor: Colors.transparent,
              tabs: const [
                Tab(text: '지하철 실시간'),
                Tab(text: '버스 정류장'),
              ],
            ),
          ),
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          // Subway Tab
          Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _subwayController,
                        decoration: const InputDecoration(
                          hintText: '지하철역 이름 (예: 강남, 판교)',
                          prefixIcon: Icon(Icons.search_rounded,
                              color: Color(0xFF8B95A1)),
                        ),
                        onSubmitted: (_) => _searchSubway(),
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _searchSubway,
                        style: ElevatedButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 20),
                        ),
                        child: const Text('조회'),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Expanded(
                  child: arrivalProvider.isLoadingSubway
                      ? const Center(
                          child: CircularProgressIndicator(color: tossBlue))
                      : arrivalProvider.subwayError != null
                          ? Center(
                              child: Text(
                                '조회 오류: ${arrivalProvider.subwayError}',
                                style:
                                    const TextStyle(color: Color(0xFFF04438)),
                              ),
                            )
                          : arrivalProvider.subwayArrivals == null
                              ? const Center(
                                  child: Text('지하철역 이름을 입력하고 조회해 보세요.',
                                      style:
                                          TextStyle(color: Color(0xFF8B95A1))),
                                )
                              : arrivalProvider.subwayArrivals!.items.isEmpty
                                  ? const Center(
                                      child: Text(
                                        '현재 운행 중인 지하철의 도착 정보가 없습니다.',
                                        style: TextStyle(
                                          color: Color(0xFF8B95A1),
                                        ),
                                        textAlign: TextAlign.center,
                                      ),
                                    )
                                  : ListView.builder(
                                      itemCount: arrivalProvider
                                          .subwayArrivals!.items.length,
                                      itemBuilder: (ctx, i) {
                                        final item = arrivalProvider
                                            .subwayArrivals!.items[i];
                                        return ArrivalItemCard(item: item);
                                      },
                                    ),
                ),
              ],
            ),
          ),

          // Bus Tab
          Padding(
            padding: const EdgeInsets.all(20.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _busStopNameController,
                        decoration: const InputDecoration(
                          labelText: '정류장 이름',
                          hintText: '예: 철산역, 솔뫼입구',
                          prefixIcon: Icon(Icons.search_rounded),
                        ),
                        onChanged: (_) {
                          if (_busCityCodeController.text.isNotEmpty ||
                              _busStationIdController.text.isNotEmpty) {
                            setState(() {
                              _busCityCodeController.clear();
                              _busStationIdController.clear();
                            });
                          }
                        },
                        onSubmitted: (_) => _searchBusStops(),
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      height: 52,
                      child: ElevatedButton(
                        onPressed:
                            _isSearchingBusStops ? null : _searchBusStops,
                        child: const Text('검색'),
                      ),
                    ),
                  ],
                ),
                if (_isSearchingBusStops)
                  const Padding(
                    padding: EdgeInsets.only(top: 12),
                    child: LinearProgressIndicator(),
                  ),
                if (_busStopSearchError != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Text(
                      _busStopSearchError!,
                      style: const TextStyle(color: Color(0xFFF04438)),
                    ),
                  ),
                if (_busStopSuggestions.isNotEmpty)
                  Container(
                    margin: const EdgeInsets.only(top: 10),
                    constraints: const BoxConstraints(maxHeight: 180),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: ListView.separated(
                      shrinkWrap: true,
                      itemCount: _busStopSuggestions.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final stop = _busStopSuggestions[index];
                        return ListTile(
                          dense: true,
                          title: Text(stop['name']?.toString() ?? ''),
                          subtitle: Text(
                            '${stop['city_name'] ?? ''} · ${stop['station_id'] ?? ''}',
                          ),
                          onTap: () => _selectBusStop(stop),
                        );
                      },
                    ),
                  ),
                if (_busStationIdController.text.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 10),
                    child: Text(
                      '선택된 정류장: ${_busStopNameController.text} '
                      '(도시코드 ${_busCityCodeController.text})',
                      style: const TextStyle(
                        fontSize: 12,
                        color: Color(0xFF4E5968),
                      ),
                    ),
                  ),
                const SizedBox(height: 12),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _searchBus,
                    child: const Text('버스 도착 정보 조회'),
                  ),
                ),
                const SizedBox(height: 16),
                Expanded(
                  child: arrivalProvider.isLoadingBus
                      ? const Center(
                          child: CircularProgressIndicator(color: tossBlue))
                      : arrivalProvider.busError != null
                          ? Center(
                              child: Text(
                                '조회 오류: ${arrivalProvider.busError}',
                                style:
                                    const TextStyle(color: Color(0xFFF04438)),
                              ),
                            )
                          : arrivalProvider.busArrivals == null
                              ? const Center(
                                  child: Text('정류장 이름을 검색하고 선택한 뒤 조회해 보세요.',
                                      style:
                                          TextStyle(color: Color(0xFF8B95A1))),
                                )
                              : arrivalProvider.busArrivals!.items.isEmpty
                                  ? const Center(
                                      child: Text(
                                        '현재 운행 중인 버스의 도착 정보가 없습니다.',
                                        style: TextStyle(
                                          color: Color(0xFF8B95A1),
                                        ),
                                        textAlign: TextAlign.center,
                                      ),
                                    )
                                  : ListView.builder(
                                      itemCount: arrivalProvider
                                          .busArrivals!.items.length,
                                      itemBuilder: (ctx, i) {
                                        final item = arrivalProvider
                                            .busArrivals!.items[i];
                                        return ArrivalItemCard(item: item);
                                      },
                                    ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
