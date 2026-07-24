import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';
import '../../providers/subject_provider.dart';
import '../../providers/study_planner_provider.dart';

class StudyPlannerCreateScreen extends ConsumerStatefulWidget {
  const StudyPlannerCreateScreen({super.key});

  @override
  ConsumerState<StudyPlannerCreateScreen> createState() =>
      _StudyPlannerCreateScreenState();
}

class _StudyPlannerCreateScreenState
    extends ConsumerState<StudyPlannerCreateScreen> {
  late List<String> _selectedSubjects;
  late DateTime _deadline;
  String _pace = 'balanced'; // balanced, intensive, relaxed (for UI display)
  int _totalStudyHoursPerWeek = 10;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _selectedSubjects = [];
    _deadline = DateTime.now().add(const Duration(days: 30));
    // Fetch subjects when screen loads
    Future.microtask(() {
      ref.read(subjectProvider.notifier).fetchSubjects();
    });
  }

  Future<void> _selectDate(BuildContext context) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _deadline,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null && picked != _deadline) {
      setState(() {
        _deadline = picked;
      });
    }
  }

  Future<void> _createPlan() async {
    if (_selectedSubjects.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select at least one subject'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      final service = ref.read(studyPlannerServiceProvider);
      
      // Determine mode based on number of subjects selected
      final mode = _selectedSubjects.length == 1 ? 'per_subject' : 'unified';
      
      final plan = await service.generatePlan(
        subjects: _selectedSubjects,
        deadline: _deadline,
        mode: mode,
        totalStudyHoursPerWeek: _totalStudyHoursPerWeek,
      );

      if (mounted) {
        // Invalidate the plans list to refresh
        ref.invalidate(activePlansProvider);
        
        // Push so the user can navigate back to the create/list screen.
        // Using go() would replace the stack and leave the user with no way back.
        context.push('/study-planner/${plan.id}/calendar');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error creating plan: ${e.toString()}'),
            backgroundColor: Colors.red,
          ),
        );
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final subjectState = ref.watch(subjectProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Create Study Plan'),
        elevation: 0,
        centerTitle: true,
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 16),
                  Text('Creating your study plan...'),
                  SizedBox(height: 8),
                  Padding(
                    padding: EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      'DreamAssist is generating a personalized study plan for you',
                      style: TextStyle(color: AppTheme.textSecondary),
                      textAlign: TextAlign.center,
                    ),
                  ),
                ],
              ),
            )
          : subjectState.isLoading && subjectState.subjects.isEmpty
              ? const Center(
                  child: CircularProgressIndicator(),
                )
              : SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Subject Selection
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Select Subjects',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 12),
                            if (subjectState.subjects.isEmpty)
                              Padding(
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                child: Center(
                                  child: Text(
                                    'No subjects found. Please create a subject first.',
                                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                          color: AppTheme.textSecondary,
                                        ),
                                    textAlign: TextAlign.center,
                                  ),
                                ),
                              )
                            else
                              Wrap(
                                spacing: 8,
                                children: subjectState.subjects.map((subject) {
                                  final isSelected =
                                      _selectedSubjects.contains(subject.name);
                                  return FilterChip(
                                    label: Text(subject.name),
                                    selected: isSelected,
                                    onSelected: (selected) {
                                      setState(() {
                                        if (selected) {
                                          _selectedSubjects.add(subject.name);
                                        } else {
                                          _selectedSubjects.remove(subject.name);
                                        }
                                      });
                                    },
                                  );
                                }).toList(),
                              ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Deadline Selection
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Study Deadline',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 12),
                            ListTile(
                              contentPadding: EdgeInsets.zero,
                              leading: const Icon(Icons.calendar_today),
                              title: Text(
                                '${_deadline.year}-${_deadline.month.toString().padLeft(2, '0')}-${_deadline.day.toString().padLeft(2, '0')}',
                              ),
                              trailing: const Icon(Icons.edit),
                              onTap: () => _selectDate(context),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Study Mode Selection
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Study Mode',
                              style: Theme.of(context).textTheme.titleMedium,
                            ),
                            const SizedBox(height: 12),
                            Column(
                              children: [
                                RadioListTile<String>(
                                  title: const Text('Relaxed'),
                                  subtitle: const Text('Flexible pace, longer timeline'),
                                  value: 'relaxed',
                                  groupValue: _pace,
                                  onChanged: (value) {
                                    if (value != null) {
                                      setState(() => _pace = value);
                                    }
                                  },
                                ),
                                RadioListTile<String>(
                                  title: const Text('Balanced'),
                                  subtitle: const Text('Moderate pace, steady progress'),
                                  value: 'balanced',
                                  groupValue: _pace,
                                  onChanged: (value) {
                                    if (value != null) {
                                      setState(() => _pace = value);
                                    }
                                  },
                                ),
                                RadioListTile<String>(
                                  title: const Text('Intensive'),
                                  subtitle: const Text('Fast pace, short timeline'),
                                  value: 'intensive',
                                  groupValue: _pace,
                                  onChanged: (value) {
                                    if (value != null) {
                                      setState(() => _pace = value);
                                    }
                                  },
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Weekly Study Hours
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Text(
                                  'Weekly Study Hours',
                                  style: Theme.of(context).textTheme.titleMedium,
                                ),
                                Text(
                                  '$_totalStudyHoursPerWeek hours',
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleMedium
                                      ?.copyWith(
                                        color: AppTheme.primaryColor,
                                      ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Slider(
                              value: _totalStudyHoursPerWeek.toDouble(),
                              min: 1,
                              max: 50,
                              divisions: 49,
                              label: '$_totalStudyHoursPerWeek hours',
                              onChanged: (value) {
                                setState(
                                  () => _totalStudyHoursPerWeek = value.toInt(),
                                );
                              },
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Create Button
                    ElevatedButton.icon(
                      onPressed: _createPlan,
                      icon: const Icon(Icons.check_circle),
                      label: const Text('Create Study Plan'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                      ),
                    ),
                    const SizedBox(height: 8),

                    // Cancel Button
                    OutlinedButton(
                      onPressed: () => context.pop(),
                      child: const Text('Cancel'),
                    ),
                    const SizedBox(height: 32),
                  ],
                ),
              ),
    );
  }
}
