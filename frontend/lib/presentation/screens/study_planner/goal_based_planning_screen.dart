// lib/screens/goal_based_planning_screen.dart
// Goal-Based Planning UI (Phase 2b)

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

class GoalBasedPlanningScreen extends StatefulWidget {
  const GoalBasedPlanningScreen({super.key});

  @override
  State<GoalBasedPlanningScreen> createState() => _GoalBasedPlanningScreenState();
}

class _GoalBasedPlanningScreenState extends State<GoalBasedPlanningScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Goal-Based Planning'),
        elevation: 0,
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Create Goal'),
            Tab(text: 'My Goals'),
            Tab(text: 'Progress'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          CreateGoalTab(),
          GoalsListTab(),
          ProgressTab(),
        ],
      ),
    );
  }
}

// ========================================================================
// CREATE GOAL TAB
// ========================================================================

class CreateGoalTab extends StatefulWidget {
  const CreateGoalTab({super.key});

  @override
  State<CreateGoalTab> createState() => _CreateGoalTabState();
}

class _CreateGoalTabState extends State<CreateGoalTab> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _titleController;
  late TextEditingController _subjectController;
  late TextEditingController _topicsController;
  late TextEditingController _targetScoreController;

  String _selectedGoalType = 'skill_acquisition';
  String _selectedPriority = 'medium';
  DateTime? _selectedDeadline;
  bool _includePrerequisites = true;

  @override
  void initState() {
    super.initState();
    _titleController = TextEditingController();
    _subjectController = TextEditingController();
    _topicsController = TextEditingController();
    _targetScoreController = TextEditingController();
  }

  @override
  void dispose() {
    _titleController.dispose();
    _subjectController.dispose();
    _topicsController.dispose();
    _targetScoreController.dispose();
    super.dispose();
  }

  void _selectDeadline() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now().add(const Duration(days: 30)),
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _selectedDeadline = picked);
    }
  }

  void _submitForm() {
    if (_formKey.currentState!.validate() && _selectedDeadline != null) {
      // API call to create goal
      final goalData = {
        'goal_title': _titleController.text,
        'goal_type': _selectedGoalType,
        'subject': _subjectController.text,
        'topics_to_cover': _topicsController.text.split(',').map((e) => e.trim()).toList(),
        'target_score': double.tryParse(_targetScoreController.text),
        'deadline': _selectedDeadline?.toIso8601String().split('T')[0],
        'priority': _selectedPriority,
        'include_prerequisites': _includePrerequisites,
      };

      print('Creating goal: $goalData');
      // TODO: Make API call

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Goal created successfully!')),
      );

      // Reset form
      _formKey.currentState!.reset();
      _titleController.clear();
      _subjectController.clear();
      _topicsController.clear();
      _targetScoreController.clear();
      setState(() => _selectedDeadline = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Goal Title
            TextFormField(
              controller: _titleController,
              decoration: InputDecoration(
                labelText: 'Goal Title',
                hintText: 'e.g., Master DSA in 2 weeks',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
              validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
            ),
            const SizedBox(height: 16),

            // Goal Type
            DropdownButtonFormField<String>(
              initialValue: _selectedGoalType,
              decoration: InputDecoration(
                labelText: 'Goal Type',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
              items: [
                'skill_acquisition',
                'exam',
                'interview_prep',
                'certification',
              ]
                  .map((type) => DropdownMenuItem(value: type, child: Text(type)))
                  .toList(),
              onChanged: (v) => setState(() => _selectedGoalType = v!),
            ),
            const SizedBox(height: 16),

            // Subject
            TextFormField(
              controller: _subjectController,
              decoration: InputDecoration(
                labelText: 'Subject',
                hintText: 'e.g., Data Structures & Algorithms',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
              validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
            ),
            const SizedBox(height: 16),

            // Topics to Cover
            TextFormField(
              controller: _topicsController,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: 'Topics to Cover',
                hintText: 'Comma-separated list (e.g., Arrays, Linked Lists, Trees)',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
              validator: (v) => v?.isEmpty ?? true ? 'Required' : null,
            ),
            const SizedBox(height: 16),

            // Target Score
            TextFormField(
              controller: _targetScoreController,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Target Score (0-100)',
                hintText: '90',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
            ),
            const SizedBox(height: 16),

            // Deadline
            ListTile(
              title: Text(
                _selectedDeadline == null
                    ? 'Select Deadline'
                    : 'Deadline: ${DateFormat('MMM d, yyyy').format(_selectedDeadline!)}',
              ),
              trailing: const Icon(Icons.calendar_today),
              onTap: _selectDeadline,
              contentPadding: EdgeInsets.zero,
            ),
            const SizedBox(height: 16),

            // Priority
            DropdownButtonFormField<String>(
              initialValue: _selectedPriority,
              decoration: InputDecoration(
                labelText: 'Priority',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              ),
              items: ['low', 'medium', 'high']
                  .map((p) => DropdownMenuItem(value: p, child: Text(p.toUpperCase())))
                  .toList(),
              onChanged: (v) => setState(() => _selectedPriority = v!),
            ),
            const SizedBox(height: 16),

            // Include Prerequisites Checkbox
            CheckboxListTile(
              title: const Text('Include Prerequisites'),
              subtitle: const Text('Auto-add prerequisite topics'),
              value: _includePrerequisites,
              onChanged: (v) => setState(() => _includePrerequisites = v!),
              contentPadding: EdgeInsets.zero,
            ),
            const SizedBox(height: 24),

            // Submit Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _submitForm,
                icon: const Icon(Icons.check),
                label: const Text('Create Goal'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ========================================================================
// GOALS LIST TAB
// ========================================================================

class GoalsListTab extends StatefulWidget {
  const GoalsListTab({super.key});

  @override
  State<GoalsListTab> createState() => _GoalsListTabState();
}

class _GoalsListTabState extends State<GoalsListTab> {
  String _selectedFilter = 'all';

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        // Filter Chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              FilterChip(
                label: const Text('All'),
                selected: _selectedFilter == 'all',
                onSelected: (s) => setState(() => _selectedFilter = 'all'),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('In Progress'),
                selected: _selectedFilter == 'in_progress',
                onSelected: (s) => setState(() => _selectedFilter = 'in_progress'),
              ),
              const SizedBox(width: 8),
              FilterChip(
                label: const Text('Completed'),
                selected: _selectedFilter == 'completed',
                onSelected: (s) => setState(() => _selectedFilter = 'completed'),
              ),
            ],
          ),
        ),
        // Goals List
        Expanded(
          child: ListView(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            children: [
              GoalCard(
                title: 'Master DSA',
                subject: 'Data Structures',
                progress: 65,
                deadline: '2 weeks',
                priority: 'high',
                onTap: () => _showGoalDetails(context),
              ),
              const SizedBox(height: 12),
              GoalCard(
                title: 'Learn Flutter',
                subject: 'Mobile Development',
                progress: 30,
                deadline: '4 weeks',
                priority: 'medium',
                onTap: () => _showGoalDetails(context),
              ),
              const SizedBox(height: 12),
              GoalCard(
                title: 'Python Mastery',
                subject: 'Programming',
                progress: 100,
                deadline: 'Completed',
                priority: 'low',
                isCompleted: true,
                onTap: () => _showGoalDetails(context),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showGoalDetails(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const GoalDetailsSheet(),
    );
  }
}

// ========================================================================
// GOAL CARD WIDGET
// ========================================================================

class GoalCard extends StatelessWidget {
  final String title;
  final String subject;
  final double progress;
  final String deadline;
  final String priority;
  final bool isCompleted;
  final VoidCallback onTap;

  const GoalCard({
    super.key,
    required this.title,
    required this.subject,
    required this.progress,
    required this.deadline,
    required this.priority,
    this.isCompleted = false,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: _getPriorityColor().withOpacity(0.2),
          child: Text('${progress.toInt()}%'),
        ),
        title: Text(title),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(subject, style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 6),
            LinearProgressIndicator(value: progress / 100),
            const SizedBox(height: 4),
            Row(
              children: [
                Icon(Icons.calendar_today, size: 12, color: Colors.grey[600]),
                const SizedBox(width: 4),
                Text(deadline, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
              ],
            ),
          ],
        ),
        trailing: Chip(
          label: Text(priority.toUpperCase()),
          backgroundColor: _getPriorityColor().withOpacity(0.2),
        ),
      ),
    );
  }

  Color _getPriorityColor() {
    switch (priority.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
}

// ========================================================================
// GOAL DETAILS SHEET
// ========================================================================

class GoalDetailsSheet extends StatelessWidget {
  const GoalDetailsSheet({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Goal Details',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              IconButton(
                icon: const Icon(Icons.close),
                onPressed: () => context.pop(),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // Goal Info
          const _InfoTile(label: 'Goal', value: 'Master DSA'),
          const SizedBox(height: 12),
          const _InfoTile(label: 'Status', value: 'In Progress'),
          const SizedBox(height: 12),
          const _InfoTile(label: 'Progress', value: '65%'),
          const SizedBox(height: 12),
          const _InfoTile(label: 'Deadline', value: '2025-02-15'),
          const SizedBox(height: 24),

          // Topics
          const Text(
            'Topics Covered',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          const Wrap(
            spacing: 8,
            children: [
              _TopicChip(label: 'Arrays', completed: true),
              _TopicChip(label: 'Linked Lists', completed: true),
              _TopicChip(label: 'Trees', completed: false),
              _TopicChip(label: 'Graphs', completed: false),
            ],
          ),
          const SizedBox(height: 24),

          // Action Buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => context.pop(),
                  child: const Text('Close'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton(
                  onPressed: () {
                    context.pop();
                    _showGeneratePlanDialog(context);
                  },
                  child: const Text('Generate Plan'),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _showGeneratePlanDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Generate Phased Plan'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Select study pace:'),
            const SizedBox(height: 16),
            Column(
              children: [
                RadioListTile(
                  title: const Text('Slow (2 hrs/day)'),
                  value: 'slow',
                  groupValue: 'moderate',
                  onChanged: (_) {},
                ),
                RadioListTile(
                  title: const Text('Moderate (3 hrs/day)'),
                  value: 'moderate',
                  groupValue: 'moderate',
                  onChanged: (_) {},
                ),
                RadioListTile(
                  title: const Text('Fast (4 hrs/day)'),
                  value: 'fast',
                  groupValue: 'moderate',
                  onChanged: (_) {},
                ),
              ],
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => context.pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              context.pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Phased plan generated!')),
              );
            },
            child: const Text('Generate'),
          ),
        ],
      ),
    );
  }
}

class _InfoTile extends StatelessWidget {
  final String label;
  final String value;

  const _InfoTile({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
      ],
    );
  }
}

class _TopicChip extends StatelessWidget {
  final String label;
  final bool completed;

  const _TopicChip({required this.label, required this.completed});

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(label),
      backgroundColor: completed ? Colors.green.withOpacity(0.2) : Colors.grey.withOpacity(0.1),
      side: BorderSide(
        color: completed ? Colors.green : Colors.grey,
      ),
    );
  }
}

// ========================================================================
// PROGRESS TAB
// ========================================================================

class ProgressTab extends StatefulWidget {
  const ProgressTab({super.key});

  @override
  State<ProgressTab> createState() => _ProgressTabState();
}

class _ProgressTabState extends State<ProgressTab> {
  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Overall Progress Card
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Overall Progress',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 16),
                LinearProgressIndicator(
                  value: 0.65,
                  minHeight: 8,
                  backgroundColor: Colors.grey[200],
                ),
                const SizedBox(height: 12),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    const Text('65% Complete'),
                    Text(
                      'On Track',
                      style: TextStyle(color: Colors.green[600], fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 24),

        // Phase Progress
        const Text(
          'Phase Progress',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        const PhaseProgressCard(
          phaseNumber: 1,
          phaseName: 'Foundations',
          progress: 100,
          isCompleted: true,
        ),
        const SizedBox(height: 12),
        const PhaseProgressCard(
          phaseNumber: 2,
          phaseName: 'Core Concepts',
          progress: 50,
          isCompleted: false,
        ),
        const SizedBox(height: 12),
        const PhaseProgressCard(
          phaseNumber: 3,
          phaseName: 'Advanced Topics',
          progress: 0,
          isCompleted: false,
        ),
        const SizedBox(height: 12),
        const PhaseProgressCard(
          phaseNumber: 4,
          phaseName: 'Practice & Integration',
          progress: 0,
          isCompleted: false,
        ),
      ],
    );
  }
}

class PhaseProgressCard extends StatelessWidget {
  final int phaseNumber;
  final String phaseName;
  final double progress;
  final bool isCompleted;

  const PhaseProgressCard({
    super.key,
    required this.phaseNumber,
    required this.phaseName,
    required this.progress,
    required this.isCompleted,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isCompleted ? Colors.green : Colors.blue,
          child: isCompleted
              ? const Icon(Icons.check, color: Colors.white)
              : Text('$phaseNumber'),
        ),
        title: Text(phaseName),
        subtitle: LinearProgressIndicator(value: progress / 100),
        trailing: Text('${progress.toInt()}%'),
      ),
    );
  }
}
