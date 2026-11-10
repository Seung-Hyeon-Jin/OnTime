import 'package:flutter/foundation.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/arrival_model.dart';

class ArrivalProvider with ChangeNotifier {
  final String authToken;

  ArrivalResponse? _subwayArrivals;
  ArrivalResponse? _busArrivals;
  bool _isLoadingSubway = false;
  bool _isLoadingBus = false;
  String? _subwayError;
  String? _busError;

  ArrivalProvider(this.authToken);

  ArrivalResponse? get subwayArrivals => _subwayArrivals;
  ArrivalResponse? get busArrivals => _busArrivals;
  bool get isLoadingSubway => _isLoadingSubway;
  bool get isLoadingBus => _isLoadingBus;
  String? get subwayError => _subwayError;
  String? get busError => _busError;

  ApiClient get _apiClient => ApiClient(token: authToken);

  Future<void> getSubwayArrivals(String stationName) async {
    _isLoadingSubway = true;
    _subwayError = null;
    notifyListeners();

    try {
      final res = await _apiClient.get(
        ApiConfig.arrivalsSubway,
        queryParams: {'station_name': stationName},
      );
      _subwayArrivals = ArrivalResponse.fromJson(res);
    } catch (e) {
      _subwayError = e.toString();
    } finally {
      _isLoadingSubway = false;
      notifyListeners();
    }
  }

  Future<void> getBusArrivals(String cityCode, String stationId) async {
    _isLoadingBus = true;
    _busError = null;
    notifyListeners();

    try {
      final res = await _apiClient.get(
        ApiConfig.arrivalsBus,
        queryParams: {
          'city_code': cityCode,
          'station_id': stationId,
        },
      );
      _busArrivals = ArrivalResponse.fromJson(res);
    } catch (e) {
      _busError = e.toString();
    } finally {
      _isLoadingBus = false;
      notifyListeners();
    }
  }
}
