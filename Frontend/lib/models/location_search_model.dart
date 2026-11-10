class LocationSearchResultItemModel {
  final String placeName;
  final String addressName;
  final String? roadAddressName;
  final double latitude;
  final double longitude;
  final String? categoryName;

  LocationSearchResultItemModel({
    required this.placeName,
    required this.addressName,
    this.roadAddressName,
    required this.latitude,
    required this.longitude,
    this.categoryName,
  });

  factory LocationSearchResultItemModel.fromJson(Map<String, dynamic> json) {
    return LocationSearchResultItemModel(
      placeName: json['place_name'] ?? '',
      addressName: json['address_name'] ?? '',
      roadAddressName: json['road_address_name'],
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      categoryName: json['category_name'],
    );
  }
}

class LocationSearchResponseModel {
  final String query;
  final List<LocationSearchResultItemModel> items;

  LocationSearchResponseModel({
    required this.query,
    required this.items,
  });

  factory LocationSearchResponseModel.fromJson(Map<String, dynamic> json) {
    return LocationSearchResponseModel(
      query: json['query'] ?? '',
      items: (json['items'] as List<dynamic>?)
              ?.map((e) => LocationSearchResultItemModel.fromJson(e))
              .toList() ??
          [],
    );
  }
}
