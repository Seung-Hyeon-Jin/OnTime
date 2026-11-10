import 'package:flutter/foundation.dart';

import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../models/route_model.dart';

class RouteSearchProvider with ChangeNotifier {
  final String authToken;

  RouteResponseModel? _searchResult;
  bool _isSearching = false;
  String? _errorMessage;

  RouteSearchProvider(this.authToken);

  RouteResponseModel? get searchResult => _searchResult;
  bool get isSearching => _isSearching;
  String? get errorMessage => _errorMessage;

  ApiClient get _apiClient => ApiClient(token: authToken);

  Future<RouteResponseModel?> searchRoutes({
    required LocationModel origin,
    required LocationModel destination,
    List<String>? transportTypes,
  }) async {
    _isSearching = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final body = {
        'origin': origin.toJson(),
        'destination': destination.toJson(),
        if (transportTypes != null) 'transport_types': transportTypes,
      };

      final res = await _apiClient.post(ApiConfig.routesSearch, body: body);
      _searchResult = RouteResponseModel.fromJson(res);
      return _searchResult;
    } catch (e) {
      _errorMessage = e.toString();
      rethrow;
    } finally {
      _isSearching = false;
      notifyListeners();
    }
  }

  void clearSearch() {
    _searchResult = null;
    _errorMessage = null;
    notifyListeners();
  }
}
