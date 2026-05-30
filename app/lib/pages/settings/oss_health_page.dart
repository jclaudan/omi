import 'dart:async';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'package:omi/backend/preferences.dart';
import 'package:omi/pages/onboarding/oss_plus/step_minio.dart';
import 'package:omi/pages/onboarding/oss_plus/step_ollama.dart';
import 'package:omi/pages/onboarding/oss_plus/step_qdrant.dart';
import 'package:omi/pages/onboarding/oss_plus/step_stt.dart';
import 'package:omi/pages/onboarding/oss_plus/step_supabase.dart';
import 'package:omi/utils/l10n_extensions.dart';

enum _HealthStatus { pending, checking, ok, slow, fail }

class _ServiceCheck {
  _ServiceCheck({
    required this.name,
    required this.url,
    this.optional = false,
    this.reconfigureBuilder,
  });

  final String name;
  final String url;
  final bool optional;
  final Widget Function(VoidCallback onDone)? reconfigureBuilder;

  _HealthStatus status = _HealthStatus.pending;
  int? latencyMs;
}

class OssHealthPage extends StatefulWidget {
  const OssHealthPage({super.key});

  @override
  State<OssHealthPage> createState() => _OssHealthPageState();
}

class _OssHealthPageState extends State<OssHealthPage> {
  late final List<_ServiceCheck> _services;
  Timer? _timer;
  DateTime? _lastChecked;

  @override
  void initState() {
    super.initState();
    _services = _buildServices();
    _runChecks();
    _timer = Timer.periodic(const Duration(seconds: 30), (_) => _runChecks());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  List<_ServiceCheck> _buildServices() {
    final p = SharedPreferencesUtil();
    String wsToHttp(String url) {
      if (url.startsWith('ws://')) return 'http://${url.substring(5)}';
      if (url.startsWith('wss://')) return 'https://${url.substring(6)}';
      return url;
    }

    String health(String base, String path) {
      if (base.isEmpty) return '';
      return '${base.trimRight().replaceAll(RegExp(r'/$'), '')}$path';
    }

    return [
      _ServiceCheck(
        name: 'Supabase',
        url: health(p.ossSupabaseUrl, '/rest/v1/'),
        reconfigureBuilder: (done) => StepSupabase(onNext: done, onBack: done),
      ),
      _ServiceCheck(
        name: 'Faster-Whisper (batch)',
        url: health(p.ossFasterWhisperBatchUrl, '/health'),
        reconfigureBuilder: (done) => StepStt(onNext: done, onBack: done),
      ),
      _ServiceCheck(
        name: 'Faster-Whisper (stream)',
        url: health(wsToHttp(p.ossFasterWhisperStreamUrl), '/health'),
        reconfigureBuilder: (done) => StepStt(onNext: done, onBack: done),
      ),
      _ServiceCheck(
        name: 'Qdrant',
        url: health(p.ossQdrantUrl, '/health'),
        reconfigureBuilder: (done) => StepQdrant(onNext: done, onBack: done),
      ),
      _ServiceCheck(
        name: 'MinIO',
        url: health(p.ossMinioEndpoint, '/minio/health/live'),
        reconfigureBuilder: (done) => StepMinio(onNext: done, onBack: done),
      ),
      _ServiceCheck(
        name: 'Ollama',
        url: health(p.ossOllamaUrl, '/api/tags'),
        optional: true,
        reconfigureBuilder: (done) => StepOllama(onNext: done, onBack: done),
      ),
    ];
  }

  Future<void> _runChecks() async {
    if (!mounted) return;
    setState(() {
      for (final s in _services) {
        s.status = _HealthStatus.checking;
        s.latencyMs = null;
      }
    });

    await Future.wait(_services.map(_checkService));

    if (mounted) setState(() => _lastChecked = DateTime.now());
  }

  Future<void> _checkService(_ServiceCheck svc) async {
    if (svc.url.isEmpty) {
      if (mounted) {
        setState(() {
          svc.status = svc.optional ? _HealthStatus.ok : _HealthStatus.fail;
          svc.latencyMs = null;
        });
      }
      return;
    }

    final sw = Stopwatch()..start();
    try {
      final resp = await http.get(Uri.parse(svc.url)).timeout(const Duration(seconds: 5));
      sw.stop();
      final ms = sw.elapsedMilliseconds;
      if (mounted) {
        setState(() {
          svc.latencyMs = ms;
          if (resp.statusCode >= 500) {
            svc.status = _HealthStatus.fail;
          } else if (ms > 2000) {
            svc.status = _HealthStatus.slow;
          } else {
            svc.status = _HealthStatus.ok;
          }
        });
      }
    } catch (_) {
      sw.stop();
      if (mounted) {
        setState(() {
          svc.status = _HealthStatus.fail;
          svc.latencyMs = null;
        });
      }
    }
  }

  void _reconfigure(_ServiceCheck svc) {
    if (svc.reconfigureBuilder == null) return;
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => Scaffold(
          backgroundColor: Colors.black,
          body: SafeArea(
            child: svc.reconfigureBuilder!(() {
              Navigator.of(context).pop();
              // Re-build services to pick up new URLs, then re-run checks.
              setState(() {
                _services
                  ..clear()
                  ..addAll(_buildServices());
              });
              _runChecks();
            }),
          ),
        ),
      ),
    );
  }

  String _formatLastChecked() {
    if (_lastChecked == null) return '';
    final diff = DateTime.now().difference(_lastChecked!);
    if (diff.inSeconds < 60) return '${diff.inSeconds}s ago';
    return '${diff.inMinutes}m ago';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(context.l10n.ossHealthTitle),
        actions: [
          TextButton(
            onPressed: _runChecks,
            child: Text(
              context.l10n.ossHealthTestNow,
              style: const TextStyle(color: Colors.white70, fontSize: 14),
            ),
          ),
        ],
      ),
      body: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 0),
            child: Text(
              context.l10n.ossHealthSubtitle,
              style: const TextStyle(color: Colors.white60, fontSize: 14),
            ),
          ),
          if (_lastChecked != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 4, 20, 0),
              child: Text(
                'Last checked: ${_formatLastChecked()}',
                style: const TextStyle(color: Colors.white38, fontSize: 12),
              ),
            ),
          const SizedBox(height: 16),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _services.length,
              separatorBuilder: (_, __) => const SizedBox(height: 1),
              itemBuilder: (ctx, i) => _ServiceTile(
                service: _services[i],
                onReconfigure: () => _reconfigure(_services[i]),
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(20),
            child: Text(
              'Auto-refreshes every 30s',
              style: const TextStyle(color: Colors.white24, fontSize: 12),
              textAlign: TextAlign.center,
            ),
          ),
        ],
      ),
    );
  }
}

class _ServiceTile extends StatelessWidget {
  const _ServiceTile({required this.service, required this.onReconfigure});

  final _ServiceCheck service;
  final VoidCallback onReconfigure;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF1C1C1E),
        borderRadius: BorderRadius.circular(12),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          _StatusDot(status: service.status),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Text(
                      service.name,
                      style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w500),
                    ),
                    if (service.optional) ...[
                      const SizedBox(width: 6),
                      Text(
                        context.l10n.ossOptional,
                        style: const TextStyle(color: Colors.white38, fontSize: 12),
                      ),
                    ],
                  ],
                ),
                const SizedBox(height: 2),
                _StatusLabel(service: service),
              ],
            ),
          ),
          if (service.reconfigureBuilder != null)
            GestureDetector(
              onTap: onReconfigure,
              child: Text(
                context.l10n.ossHealthReconfigure,
                style: const TextStyle(color: Colors.white38, fontSize: 13),
              ),
            ),
        ],
      ),
    );
  }
}

class _StatusDot extends StatelessWidget {
  const _StatusDot({required this.status});

  final _HealthStatus status;

  @override
  Widget build(BuildContext context) {
    if (status == _HealthStatus.checking) {
      return const SizedBox(
        width: 16,
        height: 16,
        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white54),
      );
    }

    final color = switch (status) {
      _HealthStatus.ok => const Color(0xFF4CAF50),
      _HealthStatus.slow => const Color(0xFFFF9800),
      _HealthStatus.fail => const Color(0xFFF44336),
      _HealthStatus.pending => Colors.white24,
      _HealthStatus.checking => Colors.white54,
    };

    return Container(
      width: 10,
      height: 10,
      decoration: BoxDecoration(color: color, shape: BoxShape.circle),
    );
  }
}

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.service});

  final _ServiceCheck service;

  @override
  Widget build(BuildContext context) {
    switch (service.status) {
      case _HealthStatus.pending:
        return const SizedBox.shrink();
      case _HealthStatus.checking:
        return Text('…', style: const TextStyle(color: Colors.white38, fontSize: 12));
      case _HealthStatus.ok:
        final ms = service.latencyMs;
        return Text(
          ms != null ? '${context.l10n.ossConnected} · ${ms}ms' : context.l10n.ossConnected,
          style: const TextStyle(color: Color(0xFF4CAF50), fontSize: 12),
        );
      case _HealthStatus.slow:
        final ms = service.latencyMs;
        return Text(
          ms != null ? '${context.l10n.ossHealthSlow} · ${ms}ms' : context.l10n.ossHealthSlow,
          style: const TextStyle(color: Color(0xFFFF9800), fontSize: 12),
        );
      case _HealthStatus.fail:
        return Text(context.l10n.ossUnreachable, style: const TextStyle(color: Color(0xFFF44336), fontSize: 12));
    }
  }
}
