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
  final Map<String, RoutineExecutionModel> _executions = {};
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

  String get _cacheKey => 'cached_routines_${authToken.hashCode}';

  Future<void> _loadCachedRoutines() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final cachedJson = prefs.getString(_cacheKey);
      if (cachedJson != null && cachedJson.isNotEmpty) {
        final List decoded = json.decode(cachedJson);
        _routines = decoded.map((j) => RoutineModel.fromJson(j)).toList();
        notifyListeners();
      }
    } catch (e) {
      debugPrint('캐시 로드 실패: $e');
    }
  }

  Future<void> _saveCachedRoutines(dynamic jsonList) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_cacheKey, json.encode(jsonList));
    } catch (e) {
      debugPrint('캐시 저장 실패: $e');
    }
  }

  Future<void> fetchRoutines() async {
    if (authToken.isEmpty) return;

    await _loadCachedRoutines();
    if (_routines.isEmpty) {
      _setLoading(true);
    }
    _errorMessage = null;

    try {
      final List res = await _apiClient.get(ApiConfig.routines);
      _routines = res.map((j) => RoutineModel.fromJson(j)).toList();
      notifyListeners();
      await _saveCachedRoutines(res);
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

      executeRoutine(newRoutine.routineId).catchError((_) => RoutineExecutionModel(
            executionId: '',
            routineId: newRoutine.routineId,
            executionDate: '',
            status: 'MONITORING',
            route: newRoutine.routePlan?.route ?? RouteResponseModel.empty(),
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

      await _saveCachedRoutines(_routines.map((r) => r.toJson()).toList());

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

      await _saveCachedRoutines(_routines.map((r) => r.toJson()).toList());
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
