import 'package:flutter/material.dart';

import 'package:omi/backend/http/api/oss.dart';
import 'package:omi/backend/http/api/oss_user.dart';
import 'package:omi/backend/preferences.dart';
import 'package:omi/pages/home/page.dart';
import 'package:omi/services/auth_service.dart';
import 'package:omi/utils/l10n_extensions.dart';

class StepAuth extends StatefulWidget {
  const StepAuth({super.key, required this.onBack});

  final VoidCallback onBack;

  @override
  State<StepAuth> createState() => _StepAuthState();
}

class _StepAuthState extends State<StepAuth> {
  final _emailCtrl = TextEditingController();
  final _passwordCtrl = TextEditingController();
  bool _isSignUp = true;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final email = _emailCtrl.text.trim();
      if (_isSignUp) {
        await AuthService.instance.signUpWithSupabase(email, _passwordCtrl.text);
      } else {
        await AuthService.instance.signInWithSupabase(email, _passwordCtrl.text);
      }
      await initOssUserProfile(email);

      // Sync OSS+ LLM provider choice with backend
      final prefs = SharedPreferencesUtil();
      final provider = prefs.ossLlmProvider;
      final apiKey = prefs.ossOpenrouterApiKey;
      final llmModel = prefs.ossOpenrouterLlmModel;
      final embeddingModel = prefs.ossOpenrouterEmbeddingModel;
      await configureOssLlmProvider(
        provider: provider,
        openrouterApiKey: provider == 'openrouter' ? apiKey : null,
        openrouterLlmModel: provider == 'openrouter' ? llmModel : null,
        openrouterEmbeddingModel: provider == 'openrouter' ? embeddingModel : null,
      );

      if (!mounted) return;
      prefs.onboardingCompleted = true;
      prefs.permissionsCompleted = true;
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const HomePageWrapper()),
        (_) => false,
      );
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
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
            _isSignUp ? context.l10n.ossAccountTitle : context.l10n.ossSignInTitle,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
          ),
          const SizedBox(height: 32),
          _Field(
            controller: _emailCtrl,
            label: context.l10n.ossEmail,
            keyboardType: TextInputType.emailAddress,
          ),
          const SizedBox(height: 16),
          _Field(
            controller: _passwordCtrl,
            label: context.l10n.ossPassword,
            obscureText: true,
          ),
          if (_error != null) ...[
            const SizedBox(height: 12),
            Text(_error!, style: const TextStyle(color: Color(0xFFF44336), fontSize: 13)),
          ],
          const SizedBox(height: 32),
          SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton(
              onPressed: _loading ? null : _submit,
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.white,
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: _loading
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black54),
                    )
                  : Text(
                      _isSignUp ? context.l10n.ossCreateAccount : context.l10n.ossSignIn,
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                    ),
            ),
          ),
          const SizedBox(height: 16),
          GestureDetector(
            onTap: () => setState(() {
              _isSignUp = !_isSignUp;
              _error = null;
            }),
            child: Text(
              _isSignUp ? context.l10n.ossHaveAccount : context.l10n.ossNoAccount,
              style: const TextStyle(color: Colors.white60, fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }
}

class _Field extends StatelessWidget {
  const _Field({
    required this.controller,
    required this.label,
    this.obscureText = false,
    this.keyboardType,
  });

  final TextEditingController controller;
  final String label;
  final bool obscureText;
  final TextInputType? keyboardType;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.white60),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.white24),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Colors.white60),
        ),
        filled: true,
        fillColor: Colors.white.withOpacity(0.05),
      ),
    );
  }
}
