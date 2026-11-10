import 'dart:async';
import 'package:flutter/material.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/location_search_model.dart';

class LocationSearchScreen extends StatefulWidget {
  final String title;

  const LocationSearchScreen({
    super.key,
    required this.title,
  });

  @override
  State<LocationSearchScreen> createState() => _LocationSearchScreenState();
}

class _LocationSearchScreenState extends State<LocationSearchScreen> {
  final _searchController = TextEditingController();
  List<LocationSearchResultItemModel> _results = [];
  bool _isSearching = false;
  String? _error;
  Timer? _debounceTimer;

  @override
  void dispose() {
    _debounceTimer?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _onQueryChanged(String text) {
    _debounceTimer?.cancel();
    if (text.trim().isEmpty) {
      setState(() {
        _results = [];
        _isSearching = false;
      });
      return;
    }

    _debounceTimer = Timer(const Duration(milliseconds: 300), () {
      _performSearch(text);
    });
  }

  Future<void> _performSearch(String query) async {
    final text = query.trim();
    if (text.isEmpty) return;

    setState(() {
      _isSearching = true;
      _error = null;
    });

    try {
      final api = ApiClient();
      final res = await api.get(
        ApiConfig.locationsSearch,
        queryParams: {'query': text},
      );
      final responseData = LocationSearchResponseModel.fromJson(res);
      setState(() {
        _results = responseData.items;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
      });
    } finally {
      setState(() {
        _isSearching = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    const tossBlue = Color(0xFF6C4DF6);
    const tossDarkText = Color(0xFF191F28);

    return Scaffold(
      backgroundColor: const Color(0xFFF2F4F6),
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: const Color(0xFFF2F4F6),
      ),
      body: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Toss Style Live Search Input Card
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                children: [
                  const Icon(Icons.search_rounded, color: tossBlue),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      autofocus: true,
                      decoration: const InputDecoration(
                        hintText: '장소명, 주소, 건물명 입력 ',
                        border: InputBorder.none,
                        enabledBorder: InputBorder.none,
                        focusedBorder: InputBorder.none,
                        fillColor: Colors.white,
                      ),
                      onChanged: _onQueryChanged,
                      onSubmitted: _performSearch,
                    ),
                  ),
                  if (_isSearching)
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: tossBlue),
                    )
                  else if (_searchController.text.isNotEmpty)
                    IconButton(
                      icon: const Icon(Icons.clear_rounded,
                          color: Color(0xFF8B95A1)),
                      onPressed: () {
                        _searchController.clear();
                        setState(() {
                          _results = [];
                        });
                      },
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            if (_results.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(left: 4.0, bottom: 8.0),
                child: Text(
                  '검색 후보 장소 (${_results.length}건)',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF8B95A1),
                  ),
                ),
              ),

            // Live Candidate Search Results List Displayed Below
            Expanded(
              child: _isSearching && _results.isEmpty
                  ? const Center(
                      child: CircularProgressIndicator(color: tossBlue),
                    )
                  : _error != null
                      ? Center(
                          child: Text(
                            '검색 중 오류 발생: $_error',
                            style: const TextStyle(color: Color(0xFFF04438)),
                          ),
                        )
                      : _results.isEmpty
                          ? Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: const [
                                  Icon(Icons.location_searching_rounded,
                                      size: 48, color: Color(0xFF8B95A1)),
                                  SizedBox(height: 12),
                                  Text(
                                    '원하는 장소나 주소를 검색해 보세요',
                                    style: TextStyle(
                                      fontSize: 15,
                                      fontWeight: FontWeight.bold,
                                      color: tossDarkText,
                                    ),
                                  ),
                                  SizedBox(height: 4),
                                  Text(
                                    '타이핑하면 아래에 연관 후보 장소가 실시간으로 나열됩니다.',
                                    style: TextStyle(
                                      fontSize: 13,
                                      color: Color(0xFF8B95A1),
                                    ),
                                    textAlign: TextAlign.center,
                                  ),
                                ],
                              ),
                            )
                          : ListView.builder(
                              itemCount: _results.length,
                              itemBuilder: (ctx, i) {
                                final item = _results[i];
                                return Container(
                                  margin: const EdgeInsets.only(bottom: 10),
                                  decoration: BoxDecoration(
                                    color: Colors.white,
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                  child: Material(
                                    color: Colors.transparent,
                                    child: ListTile(
                                      contentPadding:
                                          const EdgeInsets.symmetric(
                                              horizontal: 20, vertical: 12),
                                      leading: Container(
                                        padding: const EdgeInsets.all(10),
                                        decoration: const BoxDecoration(
                                          color: Color(0xFFE8F3FF),
                                          shape: BoxShape.circle,
                                        ),
                                        child: const Icon(
                                          Icons.place_rounded,
                                          color: tossBlue,
                                          size: 20,
                                        ),
                                      ),
                                      title: Row(
                                        children: [
                                          Expanded(
                                            child: Text(
                                              item.placeName,
                                              style: const TextStyle(
                                                fontSize: 16,
                                                fontWeight: FontWeight.bold,
                                                color: tossDarkText,
                                              ),
                                              overflow: TextOverflow.ellipsis,
                                            ),
                                          ),
                                          if (item.categoryName != null) ...[
                                            const SizedBox(width: 8),
                                            Container(
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                      horizontal: 8,
                                                      vertical: 2),
                                              decoration: BoxDecoration(
                                                color: const Color(0xFFF2F4F6),
                                                borderRadius:
                                                    BorderRadius.circular(6),
                                              ),
                                              child: Text(
                                                item.categoryName!,
                                                style: const TextStyle(
                                                  fontSize: 11,
                                                  color: Color(0xFF4E5968),
                                                ),
                                              ),
                                            ),
                                          ],
                                        ],
                                      ),
                                      subtitle: Padding(
                                        padding:
                                            const EdgeInsets.only(top: 4.0),
                                        child: Text(
                                          item.roadAddressName ??
                                              item.addressName,
                                          style: const TextStyle(
                                            fontSize: 13,
                                            color: Color(0xFF8B95A1),
                                          ),
                                        ),
                                      ),
                                      onTap: () {
                                        // 후보군 중 하나 선택 시 결과 반환
                                        Navigator.pop(context, item);
                                      },
                                    ),
                                  ),
                                );
                              },
                            ),
            ),
          ],
        ),
      ),
    );
  }
}
