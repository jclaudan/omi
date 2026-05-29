import 'package:flutter/material.dart';
import 'package:omi/pages/onboarding/mode_selector.dart';
import 'step_auth.dart';
import 'step_minio.dart';
import 'step_ollama.dart';
import 'step_qdrant.dart';
import 'step_stt.dart';
import 'step_supabase.dart';
import 'step_test.dart';
import 'step_welcome.dart';

class OssPlusOnboardingWrapper extends StatefulWidget {
  const OssPlusOnboardingWrapper({super.key});

  @override
  State<OssPlusOnboardingWrapper> createState() => _OssPlusOnboardingWrapperState();
}

class _OssPlusOnboardingWrapperState extends State<OssPlusOnboardingWrapper> {
  final PageController _controller = PageController();
  int _currentStep = 0;
  static const int _totalSteps = 8;

  void _next() {
    if (_currentStep < _totalSteps - 1) {
      setState(() => _currentStep++);
      _controller.nextPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    }
  }

  void _back() {
    if (_currentStep > 0) {
      setState(() => _currentStep--);
      _controller.previousPage(duration: const Duration(milliseconds: 300), curve: Curves.easeInOut);
    } else {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const ModeSelectorPage()));
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              child: _ProgressBar(current: _currentStep, total: _totalSteps),
            ),
            Expanded(
              child: PageView(
                controller: _controller,
                physics: const NeverScrollableScrollPhysics(),
                children: [
                  StepWelcome(onNext: _next),
                  StepSupabase(onNext: _next, onBack: _back),
                  StepStt(onNext: _next, onBack: _back),
                  StepQdrant(onNext: _next, onBack: _back),
                  StepMinio(onNext: _next, onBack: _back),
                  StepOllama(onNext: _next, onBack: _back),
                  StepTest(onNext: _next, onBack: _back),
                  StepAuth(onBack: _back),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressBar extends StatelessWidget {
  const _ProgressBar({required this.current, required this.total});

  final int current;
  final int total;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(total, (i) {
        final active = i <= current;
        return Expanded(
          child: Container(
            margin: const EdgeInsets.symmetric(horizontal: 2),
            height: 3,
            decoration: BoxDecoration(
              color: active ? Colors.white : Colors.white12,
              borderRadius: BorderRadius.circular(2),
            ),
          ),
        );
      }),
    );
  }
}
