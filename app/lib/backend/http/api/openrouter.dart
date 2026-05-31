import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:omi/utils/logger.dart';

class OpenRouterService {
  static const String baseUrl = 'https://openrouter.ai/api/v1';
  final String apiKey;

  OpenRouterService({required this.apiKey});

  Future<List<OpenRouterModel>> listModels() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/models'),
        headers: {'Authorization': 'Bearer $apiKey'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final models = (data['data'] as List)
            .map((m) => OpenRouterModel.fromJson(m))
            .toList();
        return models;
      } else {
        Logger.error('OpenRouter models fetch failed: ${response.statusCode}');
        return [];
      }
    } catch (e) {
      Logger.error('OpenRouter models error: $e');
      return [];
    }
  }

  Future<UsageInfo?> getUsageInfo() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/auth/key'),
        headers: {'Authorization': 'Bearer $apiKey'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return UsageInfo.fromJson(data);
      } else {
        Logger.error('OpenRouter usage fetch failed: ${response.statusCode}');
        return null;
      }
    } catch (e) {
      Logger.error('OpenRouter usage error: $e');
      return null;
    }
  }
}

class OpenRouterModel {
  final String id;
  final String name;
  final String? description;
  final double? costPer1kInputTokens;
  final double? costPer1kOutputTokens;
  final int? contextLength;
  final List<String> architecture;

  OpenRouterModel({
    required this.id,
    required this.name,
    this.description,
    this.costPer1kInputTokens,
    this.costPer1kOutputTokens,
    this.contextLength,
    required this.architecture,
  });

  factory OpenRouterModel.fromJson(Map<String, dynamic> json) {
    return OpenRouterModel(
      id: json['id'] ?? '',
      name: json['name'] ?? json['id'] ?? 'Unknown',
      description: json['description'],
      costPer1kInputTokens: (json['pricing']?['prompt'] ?? 0).toDouble(),
      costPer1kOutputTokens: (json['pricing']?['completion'] ?? 0).toDouble(),
      contextLength: json['context_length'],
      architecture: (json['architecture']?['modality'] as List?)?.cast<String>() ?? [],
    );
  }

  bool supportsEmbeddings() {
    return architecture.contains('text-embedding');
  }

  bool supportsCompletion() {
    return architecture.contains('text') && !supportsEmbeddings();
  }

  String get monthlyCostEstimate {
    // Rough estimate: 1M tokens per day
    final inputTokens = 1000000 * 30;
    final outputTokens = 1000000 * 30;
    final inputCost = (inputTokens / 1000) * (costPer1kInputTokens ?? 0);
    final outputCost = (outputTokens / 1000) * (costPer1kOutputTokens ?? 0);
    final total = inputCost + outputCost;
    return '\$${total.toStringAsFixed(2)}/month';
  }
}

class UsageInfo {
  final double? remainingBalance;
  final double? usedBalance;
  final DateTime? createdAt;

  UsageInfo({
    this.remainingBalance,
    this.usedBalance,
    this.createdAt,
  });

  factory UsageInfo.fromJson(Map<String, dynamic> json) {
    return UsageInfo(
      remainingBalance: (json['balance'] ?? 0).toDouble(),
      usedBalance: (json['usage'] ?? 0).toDouble(),
      createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
    );
  }

  String get balanceFormatted => '\$${remainingBalance?.toStringAsFixed(2) ?? '0.00'}';
}
