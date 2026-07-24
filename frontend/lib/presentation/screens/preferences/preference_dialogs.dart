import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../../providers/subject_profile_provider.dart';
import '../../../data/models/subject_profile_model.dart';

class AddSubjectDialog extends ConsumerStatefulWidget {
  const AddSubjectDialog({super.key});

  @override
  ConsumerState<AddSubjectDialog> createState() => _AddSubjectDialogState();
}

class _AddSubjectDialogState extends ConsumerState<AddSubjectDialog> {
  final _subjectController = TextEditingController();

  @override
  void dispose() {
    _subjectController.dispose();
    super.dispose();
  }

  void _handleTakeQuiz() {
    final subject = _subjectController.text.trim();
    if (subject.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a subject name')),
      );
      return;
    }

    Navigator.pop(context);
    context.push('/diagnostic-quiz/$subject');
  }

  void _handleSkipQuiz() {
    final subject = _subjectController.text.trim();
    if (subject.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a subject name')),
      );
      return;
    }

    Navigator.pop(context);
    showDialog(
      context: context,
      builder: (context) => _ManualPreferencesDialog(subject: subject),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Add New Subject'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            controller: _subjectController,
            decoration: const InputDecoration(
              labelText: 'Subject Name',
              hintText: 'e.g., Data Structures, Machine Learning',
              prefixIcon: Icon(Icons.subject),
            ),
            textCapitalization: TextCapitalization.words,
          ),
          const SizedBox(height: 16),
          Text(
            'Would you like to take a diagnostic quiz to assess your level?',
            style: Theme.of(context).textTheme.bodySmall,textAlign: TextAlign.center,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: _handleSkipQuiz,
          child: const Text('Skip Quiz'),
        ),
        ElevatedButton(
          onPressed: _handleTakeQuiz,
          child: const Text('Take Quiz'),
        ),
      ],
    );
  }
}

class EditSubjectDialog extends ConsumerStatefulWidget {
  final SubjectProfileModel profile;

  const EditSubjectDialog({super.key, required this.profile});

  @override
  ConsumerState<EditSubjectDialog> createState() => _EditSubjectDialogState();
}

class _EditSubjectDialogState extends ConsumerState<EditSubjectDialog> {
  late String _level;
  late String _studyPace;
  late String _studyStyle;
  late String _breakPreference;

  @override
  void initState() {
    super.initState();
    _level = widget.profile.level;
    _studyPace = widget.profile.studyPace;
    _studyStyle = widget.profile.studyStyle;
    _breakPreference = widget.profile.breakPreference;
  }

  Future<void> _handleSave() async {
    final success = await ref.read(subjectProfileProvider.notifier).updateProfile(
          subject: widget.profile.subject,
          level: _level,
          studyPace: _studyPace,
          studyStyle: _studyStyle,
          breakPreference: _breakPreference,
        );

    if (mounted) {
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Preferences updated')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                ref.read(subjectProfileProvider).error ?? 'Failed to update'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Edit ${widget.profile.subject}'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Level', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'beginner', label: Text('Beginner')),
                ButtonSegment(value: 'intermediate', label: Text('Intermediate')),
                ButtonSegment(value: 'advanced', label: Text('Advanced')),
              ],
              selected: {_level},
              onSelectionChanged: (Set<String> selected) {
                setState(() => _level = selected.first);
              },
            ),
            const SizedBox(height: 16),
            Text('Study Pace', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'slow', label: Text('Slow')),
                ButtonSegment(value: 'moderate', label: Text('Moderate')),
                ButtonSegment(value: 'fast', label: Text('Fast')),
              ],
              selected: {_studyPace},
              onSelectionChanged: (Set<String> selected) {
                setState(() => _studyPace = selected.first);
              },
            ),
            const SizedBox(height: 16),
            Text('Study Style', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _studyStyle,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: const [
                DropdownMenuItem(value: 'theory-focused', child: Text('Theory Focused')),
                DropdownMenuItem(value: 'practice-focused', child: Text('Practice Focused')),
                DropdownMenuItem(value: 'mixed', child: Text('Mixed')),
                DropdownMenuItem(value: 'visual', child: Text('Visual')),
                DropdownMenuItem(value: 'problem-solving based', child: Text('Problem-Solving Based')),
              ],
              onChanged: (value) {
                if (value != null) setState(() => _studyStyle = value);
              },
            ),
            const SizedBox(height: 16),
            Text('Break Preference', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _breakPreference,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: const [
                DropdownMenuItem(value: '5 min after 25 min', child: Text('5 min after 25 min (Pomodoro)')),
                DropdownMenuItem(value: '10 min after 45 min', child: Text('10 min after 45 min')),
                DropdownMenuItem(value: '15 min after 60 min', child: Text('15 min after 60 min')),
                DropdownMenuItem(value: '20 min after 90 min', child: Text('20 min after 90 min')),
              ],
              onChanged: (value) {
                if (value != null) setState(() => _breakPreference = value);
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _handleSave,
          child: const Text('Save'),
        ),
      ],
    );
  }
}

class _ManualPreferencesDialog extends ConsumerStatefulWidget {
  final String subject;

  const _ManualPreferencesDialog({required this.subject});

  @override
  ConsumerState<_ManualPreferencesDialog> createState() =>
      _ManualPreferencesDialogState();
}

class _ManualPreferencesDialogState
    extends ConsumerState<_ManualPreferencesDialog> {
  String _level = 'intermediate';
  String _studyPace = 'moderate';
  String _studyStyle = 'mixed';
  String _breakPreference = '10 min after 45 min';

  Future<void> _handleCreate() async {
    final profile = SubjectProfileCreate(
      subject: widget.subject,
      level: _level,
      studyPace: _studyPace,
      studyStyle: _studyStyle,
      breakPreference: _breakPreference,
    );

    final success =
        await ref.read(subjectProfileProvider.notifier).createProfileManually(profile);

    if (mounted) {
      if (success) {
        Navigator.pop(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${widget.subject} added successfully')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
                ref.read(subjectProfileProvider).error ?? 'Failed to create profile'),
            backgroundColor: AppTheme.errorColor,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text('Set Preferences for ${widget.subject}'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Level', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'beginner', label: Text('Beginner')),
                ButtonSegment(value: 'intermediate', label: Text('Intermediate')),
                ButtonSegment(value: 'advanced', label: Text('Advanced')),
              ],
              selected: {_level},
              onSelectionChanged: (Set<String> selected) {
                setState(() => _level = selected.first);
              },
            ),
            const SizedBox(height: 16),
            Text('Study Pace', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'slow', label: Text('Slow')),
                ButtonSegment(value: 'moderate', label: Text('Moderate')),
                ButtonSegment(value: 'fast', label: Text('Fast')),
              ],
              selected: {_studyPace},
              onSelectionChanged: (Set<String> selected) {
                setState(() => _studyPace = selected.first);
              },
            ),
            const SizedBox(height: 16),
            Text('Study Style', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _studyStyle,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: const [
                DropdownMenuItem(value: 'theory-focused', child: Text('Theory Focused')),
                DropdownMenuItem(value: 'practice-focused', child: Text('Practice Focused')),
                DropdownMenuItem(value: 'mixed', child: Text('Mixed')),
                DropdownMenuItem(value: 'visual', child: Text('Visual')),
                DropdownMenuItem(value: 'problem-solving based', child: Text('Problem-Solving Based')),
              ],
              onChanged: (value) {
                if (value != null) setState(() => _studyStyle = value);
              },
            ),
            const SizedBox(height: 16),
            Text('Break Preference', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              initialValue: _breakPreference,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: const [
                DropdownMenuItem(value: '5 min after 25 min', child: Text('5 min after 25 min (Pomodoro)')),
                DropdownMenuItem(value: '10 min after 45 min', child: Text('10 min after 45 min')),
                DropdownMenuItem(value: '15 min after 60 min', child: Text('15 min after 60 min')),
                DropdownMenuItem(value: '20 min after 90 min', child: Text('20 min after 90 min')),
              ],
              onChanged: (value) {
                if (value != null) setState(() => _breakPreference = value);
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _handleCreate,
          child: const Text('Create'),
        ),
      ],
    );
  }
}
