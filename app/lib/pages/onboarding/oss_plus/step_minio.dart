import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/utils/l10n_extensions.dart';
import '_shared.dart';

class StepMinio extends StatefulWidget {
  const StepMinio({super.key, required this.onNext, required this.onBack});

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  State<StepMinio> createState() => _StepMinioState();
}

class _StepMinioState extends State<StepMinio> {
  final _endpointController = TextEditingController();
  final _accessKeyController = TextEditingController();
  final _secretKeyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _endpointController.text = SharedPreferencesUtil().ossMinioEndpoint;
    _accessKeyController.text = SharedPreferencesUtil().ossMinioAccessKey;
    _secretKeyController.text = SharedPreferencesUtil().ossMinioSecretKey;
  }

  @override
  void dispose() {
    _endpointController.dispose();
    _accessKeyController.dispose();
    _secretKeyController.dispose();
    super.dispose();
  }

  bool get _canContinue =>
      _endpointController.text.trim().isNotEmpty &&
      _accessKeyController.text.trim().isNotEmpty &&
      _secretKeyController.text.trim().isNotEmpty;

  void _save() {
    SharedPreferencesUtil().ossMinioEndpoint = _endpointController.text.trim();
    SharedPreferencesUtil().ossMinioAccessKey = _accessKeyController.text.trim();
    SharedPreferencesUtil().ossMinioSecretKey = _secretKeyController.text.trim();
  }

  @override
  Widget build(BuildContext context) {
    return OssStepScaffold(
      onBack: widget.onBack,
      serviceName: 'MinIO',
      subtitle: context.l10n.ossStorageSubtitle,
      icon: Icons.storage,
      child: Column(
        children: [
          OssTextField(
            controller: _endpointController,
            label: 'Endpoint',
            hint: 'http://localhost:9000',
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          OssTextField(
            controller: _accessKeyController,
            label: 'Access Key',
            hint: 'minioadmin',
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          OssTextField(
            controller: _secretKeyController,
            label: 'Secret Key',
            hint: '••••••••',
            obscure: true,
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 32),
          OssNextButton(
            enabled: _canContinue,
            label: context.l10n.continueButton,
            onPressed: () {
              _save();
              widget.onNext();
            },
          ),
        ],
      ),
    );
  }
}
