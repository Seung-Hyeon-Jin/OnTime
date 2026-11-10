import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/route_model.dart';
import '../models/routine_model.dart';

class RoutineProvider with ChangeNotifier {
  String authToken;

  List<RoutineModel> _routines = [];
  Map<String, RoutineExecutionModel> _executions = {};
  bool _isLoading = false;
  String? _errorMessage;
  bool _isDisposed = false;

  RoutineProvider(this.authToken) {
    if (authToken.isNotEmpty) {
      _loadCachedRoutines();
    }
  }

  void updateToken(String newToken) {
    if (authToken != newToken) {
      authToken = newToken;
      if (authToken.isNotEmpty) {
        _loadCachedRoutines();
      }
    }
  }

  @override
  void dispose() {
    _isDisposed = true;
    super.dispose();
  }

  @override
  void notifyListeners() {
    if (!_isDisposed) {
      super.notifyListeners();
    }
  }

  List<RoutineModel> get routines => _routines;
  Map<String, RoutineExecutionModel> get executions => _executions;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;

  ApiClient get _apiClient => ApiClient(token: authToken);

  Future<void> _loadCachedRoutines() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cacheKey = 'cached_routines_${authToken.hashCode}';
      final cachedJson = prefs.getString(cacheKey);
      if (cachedJson != null && cachedJson.isNotEmpty) {
        final List decoded = json.decode(cachedJson);
        _routines = decoded.map((j) => RoutineModel.fromJson(j)).toList();
        notifyListeners();
      }
    } catch (_) {}
  }

  Future<void> fetchRoutines() async {
    if (authToken.isEmpty) return;

    // 1. 디바이스 로컬 저장소 캐시 먼저 로드 (0ms 로딩)
    await _loadCachedRoutines();

    // 이미 캐시 데이터가 있으면 로딩 상태 스킵
    if (_routines.isEmpty) {
      _setLoading(true);
    }

    _errorMessage = null;

    try {
      final List res = await _apiClient.get(ApiConfig.routines);
      _routines = res.map((j) => RoutineModel.fromJson(j)).toList();
      notifyListeners();

      // 2. 최신 루틴 데이터를 디바이스 저장소에 캐싱
      try {
        final prefs = await SharedPreferences.getInstance();
        final cacheKey = 'cached_routines_${authToken.hashCode}';
        await prefs.setString(cacheKey, json.encode(res));
      } catch (_) {}
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  Future<void> sendTestNotification(String routineId) async {
    try {
      await _apiClient.post(ApiConfig.routineTestNotification(routineId));
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }
  }

  Future<RoutineModel> createRoutine({
    required String name,
    required String departureStop,
    required String arrivalStop,
    required List<String> scheduledDays,
    required String departureTime,
    required int notifyMinsBefore,
    bool enabled = true,
    bool excludeHolidays = false,
    Map<String, dynamic>? origin,
    Map<String, dynamic>? destination,
    int selectedRouteIndex = 0,
  }) async {
    _setLoading(true);
    try {
      final body = {
        'name': name,
        'departure_stop': departureStop,
        'arrival_stop': arrivalStop,
        'scheduled_days': scheduledDays,
        'departure_time': departureTime,
        'notify_mins_before': notifyMinsBefore,
        'enabled': enabled,
        'exclude_holidays': excludeHolidays,
        'selected_route_index': selectedRouteIndex,
        if (origin != null) 'origin': origin,
        if (destination != null) 'destination': destination,
      };

      final res = await _apiClient.post(ApiConfig.routines, body: body);
      final newRoutine = RoutineModel.fromJson(res);
      _routines.add(newRoutine);
      notifyListeners();

      // 새 루틴 추가 즉시 실시간 대중교통 정보 비동기 수신
      final fallbackRoute = RouteResponseModel.empty();
      executeRoutine(newRoutine.routineId).catchError((_) => RoutineExecutionModel(
            executionId: '',
            routineId: newRoutine.routineId,
            executionDate: '',
            status: 'MONITORING',
            route: newRoutine.routePlan?.route ?? fallbackRoute,
            lastCheckedAt: '',
          ));
      return newRoutine;
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    } finally {
      _setLoading(false);
    }
  }

  Future<RoutineModel> updateRoutine({
    required String routineId,
    required String name,
    required String departureStop,
    required String arrivalStop,
    required List<String> scheduledDays,
    required String departureTime,
    required int notifyMinsBefore,
    bool enabled = true,
    bool excludeHolidays = false,
    Map<String, dynamic>? origin,
    Map<String, dynamic>? destination,
    int selectedRouteIndex = 0,
  }) async {
    _setLoading(true);
    try {
      final body = {
        'name': name,
        'departure_stop': departureStop,
        'arrival_stop': arrivalStop,
        'scheduled_days': scheduledDays,
        'departure_time': departureTime,
        'notify_mins_before': notifyMinsBefore,
        'enabled': enabled,
        'exclude_holidays': excludeHolidays,
        'selected_route_index': selectedRouteIndex,
        if (origin != null) 'origin': origin,
        if (destination != null) 'destination': destination,
      };

      final res =
          await _apiClient.put(ApiConfig.routineDetail(routineId), body: body);
      final updatedRoutine = RoutineModel.fromJson(res);

      final index = _routines.indexWhere((r) => r.routineId == routineId);
      if (index != -1) {
        _routines[index] = updatedRoutine;
        notifyListeners();
      }

      // 캐시 갱신
      try {
        final prefs = await SharedPreferences.getInstance();
        final cacheKey = 'cached_routines_${authToken.hashCode}';
        await prefs.setString(
            cacheKey, json.encode(_routines.map((r) => r.toJson()).toList()));
      } catch (_) {}

      // 수정 후 비동기 실시간 정보 수신
      executeRoutine(updatedRoutine.routineId).catchError((_) => RoutineExecutionModel(
            executionId: '',
            routineId: updatedRoutine.routineId,
            executionDate: '',
            status: 'MONITORING',
            route: updatedRoutine.routePlan?.route ?? RouteResponseModel.empty(),
            lastCheckedAt: '',
          ));

      return updatedRoutine;
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> deleteRoutine(String routineId) async {
    try {
      await _apiClient.delete(ApiConfig.routineDetail(routineId));
      _routines.removeWhere((r) => r.routineId == routineId);
      _executions.remove(routineId);
      notifyListeners();

      // 캐시 갱신
      try {
        final prefs = await SharedPreferences.getInstance();
        final cacheKey = 'cached_routines_${authToken.hashCode}';
        final jsonList = _routines.map((r) => {
          'routine_id': r.routineId,
          'user_id': r.userId,
          'name': r.name,
          'departure_stop': r.departureStop,
          'arrival_stop': r.arrivalStop,
          'scheduled_days': r.scheduledDays,
          'departure_time': r.departureTime,
          'notify_mins_before': r.notifyMinsBefore,
          'enabled': r.enabled,
        }).toList();
        await prefs.setString(cacheKey, json.encode(jsonList));
      } catch (_) {}
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }
  }

  Future<RoutineExecutionModel> executeRoutine(String routineId) async {
    try {
      final res = await _apiClient.post(ApiConfig.routineExecute(routineId));
      final execution = RoutineExecutionModel.fromJson(res);
      _executions[routineId] = execution;
      notifyListeners();
      return execution;
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    }
  }

  void _setLoading(bool value) {
    _isLoading = value;
    notifyListeners();
  }
}
