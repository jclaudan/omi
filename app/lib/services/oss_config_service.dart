import 'package:http/http.dart' as http;
import 'package:omi/backend/preferences.dart';
import 'dart:convert';
import 'package:omi/utils/logger.dart';

class OssConfigService {
  static final OssConfigService _instance = OssConfigService._internal();
  static OssConfigService get instance => _instance;
  OssConfigService._internal();

  Future<bool> saveOpenRouterConfig({
    required String apiKey,
    required String llmModel,
    required String embeddingModel,
  }) async {
    try {
      final prefs = SharedPreferencesUtil();
      final apiBaseUrl = prefs.apiBaseUrl;

      if (apiBaseUrl.isEmpty) {
        Logger.error('API base URL not configured');
        return false;
      }

      final token = prefs.authToken;
      if (token.isEmpty) {
        Logger.error('Auth token not available');
        return false;
      }

      final body = jsonEncode({
        'provider': 'openrouter',
        'openrouter': {
          'api_key': apiKey,
          'llm_model': llmModel,
          'embedding_model': embeddingModel,
        },
      });

      final response = await http.post(
        Uri.parse('$apiBaseUrl/v1/oss/configure-llm'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: body,
      );

      if (response.statusCode == 200) {
        Logger.info('OpenRouter config saved successfully');
        return true;
      } else {
        Logger.error('Failed to save config: ${response.statusCode} ${response.body}');
        return false;
      }
    } catch (e) {
      Logger.error('Error saving OpenRouter config: $e');
      return false;
    }
  }

  Future<bool> saveOllamaConfig() async {
    try {
      final prefs = SharedPreferencesUtil();
      final apiBaseUrl = prefs.apiBaseUrl;

      if (apiBaseUrl.isEmpty) {
        Logger.error('API base URL not configured');
        return false;
      }

      final token = prefs.authToken;
      if (token.isEmpty) {
        Logger.error('Auth token not available');
        return false;
      }

      final body = jsonEncode({'provider': 'ollama'});

      final response = await http.post(
        Uri.parse('$apiBaseUrl/v1/oss/configure-llm'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: body,
      );

      if (response.statusCode == 200) {
        Logger.info('Ollama config saved successfully');
        return true;
      } else {
        Logger.error('Failed to save config: ${response.statusCode} ${response.body}');
        return false;
      }
    } catch (e) {
      Logger.error('Error saving Ollama config: $e');
      return false;
    }
  }
}
