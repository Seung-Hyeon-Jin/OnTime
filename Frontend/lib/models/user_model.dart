class UserModel {
  final String userId;
  final String email;
  final String name;
  final String? deviceToken;
  final bool notificationsEnabled;

  UserModel({
    required this.userId,
    required this.email,
    required this.name,
    this.deviceToken,
    this.notificationsEnabled = true,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      userId: json['user_id'] ?? '',
      email: json['email'] ?? '',
      name: json['name'] ?? '',
      deviceToken: json['device_token'],
      notificationsEnabled: json['notifications_enabled'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'email': email,
      'name': name,
      'device_token': deviceToken,
      'notifications_enabled': notificationsEnabled,
    };
  }
}

class TokenResponse {
  final String accessToken;
  final String tokenType;

  TokenResponse({
    required this.accessToken,
    this.tokenType = 'bearer',
  });

  factory TokenResponse.fromJson(Map<String, dynamic> json) {
    return TokenResponse(
      accessToken: json['access_token'] ?? '',
      tokenType: json['token_type'] ?? 'bearer',
    );
  }
}
