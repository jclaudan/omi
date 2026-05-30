import 'dart:convert';

import 'package:omi/backend/http/shared.dart';
import 'package:omi/env/env.dart';
import 'package:omi/utils/logger.dart';

/// Calls the backend to initialize (or confirm) the Supabase user profile.
/// Should be invoked once after Supabase sign-up or sign-in.
Future<bool> initOssUserProfile(String email) async {
  try {
    final response = await makeApiCall(
      url: '${Env.apiBaseUrl}v1/oss/profile/init',
      headers: {},
      method: 'POST',
      body: jsonEncode({'email': email}),
    );
    if (response == null) return false;
    return response.statusCode == 200;
  } catch (e) {
    Logger.debug('initOssUserProfile error: $e');
    return false;
  }
}
