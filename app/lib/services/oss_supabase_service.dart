import 'package:supabase_flutter/supabase_flutter.dart';

import 'package:omi/backend/preferences.dart';
import 'package:omi/utils/logger.dart';

class OssSupabaseService {
  static final OssSupabaseService _instance = OssSupabaseService._internal();
  static OssSupabaseService get instance => _instance;
  OssSupabaseService._internal();

  bool _initialized = false;

  Future<void> initialize() async {
    if (_initialized) return;

    // Auto-initialize with default OSS+ values if not explicitly configured
    var url = SharedPreferencesUtil().ossSupabaseUrl;
    var anonKey = SharedPreferencesUtil().ossSupabaseAnonKey;

    if (url.isEmpty) {
      url = 'http://localhost:8000'; // Default OSS+ PostgREST endpoint
      SharedPreferencesUtil().ossSupabaseUrl = url;
    }

    if (anonKey.isEmpty) {
      anonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV4YW1wbGUiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNDIwOTIwMCwiZXhwIjoxNjQ1ODQ1MjAwfQ.UJTIOA1f9sErKgE6bpmArrEGghU-3vhVYWMuNxqHCCk'; // Default anon key from .env.selfhosted
      SharedPreferencesUtil().ossSupabaseAnonKey = anonKey;
    }

    await Supabase.initialize(url: url, anonKey: anonKey);
    _initialized = true;
    Logger.debug('OssSupabaseService: initialized with $url (OSS+ mode)');
  }

  bool get isInitialized => _initialized;

  SupabaseClient get client => Supabase.instance.client;

  bool isSignedIn() => _initialized && client.auth.currentUser != null;

  /// Returns the Supabase JWT access token, refreshing if needed.
  Future<String?> getAccessToken() async {
    if (!_initialized) return null;
    try {
      final session = await client.auth.refreshSession();
      return session.session?.accessToken;
    } catch (e) {
      Logger.debug('OssSupabaseService: getAccessToken error: $e');
      return client.auth.currentSession?.accessToken;
    }
  }

  User? get currentUser => _initialized ? client.auth.currentUser : null;

  Future<AuthResponse> signUp(String email, String password) {
    return client.auth.signUp(email: email, password: password);
  }

  Future<AuthResponse> signInWithPassword(String email, String password) {
    return client.auth.signInWithPassword(email: email, password: password);
  }

  Future<void> signOut() async {
    if (!_initialized) return;
    await client.auth.signOut();
  }
}
