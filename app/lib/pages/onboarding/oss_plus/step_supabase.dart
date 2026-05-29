import 'package:flutter/material.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/utils/l10n_extensions.dart';
import '_shared.dart';

class StepSupabase extends StatefulWidget {
  const StepSupabase({super.key, required this.onNext, required this.onBack});

  final VoidCallback onNext;
  final VoidCallback onBack;

  @override
  State<StepSupabase> createState() => _StepSupabaseState();
}

class _StepSupabaseState extends State<StepSupabase> {
  final _urlController = TextEditingController();
  final _anonKeyController = TextEditingController();
  final _serviceKeyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _urlController.text = SharedPreferencesUtil().ossSupabaseUrl;
    _anonKeyController.text = SharedPreferencesUtil().ossSupabaseAnonKey;
    _serviceKeyController.text = SharedPreferencesUtil().ossSupabaseServiceKey;
  }

  @override
  void dispose() {
    _urlController.dispose();
    _anonKeyController.dispose();
    _serviceKeyController.dispose();
    super.dispose();
  }

  bool get _canContinue => _urlController.text.trim().isNotEmpty && _anonKeyController.text.trim().isNotEmpty;

  void _save() {
    SharedPreferencesUtil().ossSupabaseUrl = _urlController.text.trim();
    SharedPreferencesUtil().ossSupabaseAnonKey = _anonKeyController.text.trim();
    SharedPreferencesUtil().ossSupabaseServiceKey = _serviceKeyController.text.trim();
  }

  @override
  Widget build(BuildContext context) {
    return OssStepScaffold(
      onBack: widget.onBack,
      serviceName: 'Supabase',
      subtitle: context.l10n.ossAuthSubtitle,
      icon: Icons.security,
      child: Column(
        children: [
          OssTextField(
            controller: _urlController,
            label: 'Project URL',
            hint: 'https://your-project.supabase.co',
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          OssTextField(
            controller: _anonKeyController,
            label: 'Anon Key',
            hint: 'eyJhbGciOi...',
            obscure: true,
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          OssTextField(
            controller: _serviceKeyController,
            label: 'Service Role Key',
            hint: 'eyJhbGciOi...',
            obscure: true,
            optionalLabel: context.l10n.ossOptional,
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
