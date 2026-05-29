import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:omi/backend/preferences.dart';
import 'package:omi/pages/home/page.dart';
import 'package:omi/utils/l10n_extensions.dart';

class StepTest extends StatefulWidget {
  const StepTest({super.key, required this.onBack});

  final VoidCallback onBack;

  @override
  State<StepTest> createState() => _StepTestState();
}

enum _Status { pending, testing, ok, fail }

class _ServiceEntry {
  _ServiceEntry(this.name, {this.optional = false});
  final String name;
  final bool optional;
  _Status status = _Status.pending;
}

class _StepTestState extends State<StepTest> {
  late final List<_ServiceEntry> _services;
  bool _tested = false;

  bool get _allRequiredOk => _services.where((s) => !s.optional).every((s) => s.status == _Status.ok);

  @override
  void initState() {
    super.initState();
    _services = [
      _ServiceEntry('Supabase'),
      _ServiceEntry('Faster-Whisper (batch)'),
      _ServiceEntry('Faster-Whisper (stream)'),
      _ServiceEntry('Qdrant'),
      _ServiceEntry('MinIO'),
      _ServiceEntry('Ollama', optional: true),
    ];
    WidgetsBinding.instance.addPostFrameCallback((_) => _runTests());
  }

  Future<void> _runTests() async {
    setState(() {
      _tested = false;
      for (final s in _services) s.status = _Status.testing;
    });

    final prefs = SharedPreferencesUtil();
    final urls = [
      _healthUrl(prefs.ossSupabaseUrl, '/rest/v1/'),
      _healthUrl(prefs.ossFasterWhisperBatchUrl, '/health'),
      _healthUrl(_wsToHttp(prefs.ossFasterWhisperStreamUrl), '/health'),
      _healthUrl(prefs.ossQdrantUrl, '/health'),
      _healthUrl(prefs.ossMinioEndpoint, '/minio/health/live'),
      _healthUrl(prefs.ossOllamaUrl, '/api/tags'),
    ];

    for (int i = 0; i < _services.length; i++) {
      final url = urls[i];
      _Status status;
      if (url.isEmpty) {
        status = _services[i].optional ? _Status.ok : _Status.fail;
      } else {
        status = await _ping(url);
      }
      if (mounted) setState(() => _services[i].status = status);
    }

    if (mounted) setState(() => _tested = true);
  }

  String _healthUrl(String base, String path) {
    if (base.isEmpty) return '';
    return '${base.trimRight().replaceAll(RegExp(r'/$'), '')}$path';
  }

  String _wsToHttp(String url) {
    if (url.startsWith('ws://')) return 'http://${url.substring(5)}';
    if (url.startsWith('wss://')) return 'https://${url.substring(6)}';
    return url;
  }

  Future<_Status> _ping(String url) async {
    try {
      final response = await http.get(Uri.parse(url)).timeout(const Duration(seconds: 5));
      return response.statusCode < 500 ? _Status.ok : _Status.fail;
    } catch (_) {
      return _Status.fail;
    }
  }

  void _finish() {
    SharedPreferencesUtil().onboardingCompleted = true;
    SharedPreferencesUtil().permissionsCompleted = true;
    Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const HomePageWrapper()), (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: widget.onBack,
            child: const Icon(Icons.arrow_back_ios, color: Colors.white70, size: 20),
          ),
          const SizedBox(height: 24),
          Text(
            context.l10n.ossConnectionTestTitle,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 8),
          if (!_tested)
            Text(context.l10n.ossConnectionTestSubtitle, style: TextStyle(fontSize: 14, color: Colors.grey[500])),
          const SizedBox(height: 24),
          Expanded(
            child: ListView.separated(
              itemCount: _services.length,
              separatorBuilder: (_, __) => Divider(color: Colors.white.withOpacity(0.06), height: 1),
              itemBuilder: (ctx, i) => _ServiceRow(service: _services[i]),
            ),
          ),
          if (_tested) ...[
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton(
                onPressed: _allRequiredOk ? _finish : _runTests,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.white,
                  foregroundColor: Colors.black,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: Text(
                  _allRequiredOk ? context.l10n.ossFinish : 'Retry',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                ),
              ),
            ),
          ],
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

class _ServiceRow extends StatelessWidget {
  const _ServiceRow({required this.service});

  final _ServiceEntry service;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 14),
      child: Row(
        children: [
          Expanded(
            child: Row(
              children: [
                Text(
                  service.name,
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w500, color: Colors.white),
                ),
                if (service.optional) ...[
                  const SizedBox(width: 6),
                  Text(context.l10n.ossOptional, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                ],
              ],
            ),
          ),
          _StatusBadge(status: service.status),
        ],
      ),
    );
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({required this.status});

  final _Status status;

  @override
  Widget build(BuildContext context) {
    switch (status) {
      case _Status.pending:
        return const SizedBox(width: 20, height: 20);
      case _Status.testing:
        return const SizedBox(
          width: 20,
          height: 20,
          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white54),
        );
      case _Status.ok:
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle, color: Color(0xFF4CAF50), size: 20),
            const SizedBox(width: 6),
            Text(context.l10n.ossConnected, style: const TextStyle(color: Color(0xFF4CAF50), fontSize: 13)),
          ],
        );
      case _Status.fail:
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.cancel, color: Color(0xFFF44336), size: 20),
            const SizedBox(width: 6),
            Text(context.l10n.ossUnreachable, style: const TextStyle(color: Color(0xFFF44336), fontSize: 13)),
          ],
        );
    }
  }
}
