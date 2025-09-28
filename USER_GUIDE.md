# Mission Commander User Guide

## Getting Started

### First Launch

1. **Open the Application**
   - Navigate to http://localhost:3000 in your web browser
   - You'll see the Mission Commander dashboard

2. **System Health Check**
   - The dashboard will show system status indicators
   - Green indicators mean all systems are operational
   - Yellow/Red indicators require attention

3. **Register Your First Drone**
   - Click "Drone Management" in the navigation
   - Add your drone's details (ID, name, capabilities)
   - The system will automatically detect compatible drones

### Creating Your First Mission

#### Step 1: Natural Language Planning
1. Go to the **Mission Planning** page
2. In the chat interface, describe your mission:
   ```
   "Search the collapsed building for survivors"
   ```
3. The AI will ask clarifying questions:
   - Location details
   - Search priorities
   - Environmental conditions
   - Time constraints

#### Step 2: Area Selection
1. The AI may ask you to select the search area on the map
2. Click on the map to define the search boundaries
3. Drag to create polygons for complex areas
4. The system will calculate optimal coverage patterns

#### Step 3: Mission Configuration
1. Review the AI's suggested parameters:
   - Search altitude (typically 20-50 meters)
   - Flight speed (thorough vs fast)
   - Recording mode (continuous vs event-triggered)
   - Drone assignments

2. Make adjustments as needed:
   - Change altitude for better visibility
   - Adjust speed for thoroughness vs speed
   - Modify recording preferences

#### Step 4: Mission Approval
1. Review the complete mission plan
2. Check estimated duration and coverage
3. Approve the mission when ready
4. Drones will automatically begin their search patterns

## Mission Execution

### Real-time Monitoring

#### Dashboard View
- **Mission Overview**: Current status and progress
- **Drone Status**: Battery levels, positions, and health
- **Live Map**: Real-time drone positions and search progress
- **Analytics**: Performance metrics and trends

#### Key Indicators to Monitor
- **Battery Levels**: Should remain above 20%
- **Signal Strength**: Should be above 70%
- **Coverage Progress**: Track search area completion
- **Discovery Alerts**: Immediate notifications of findings

### Handling Discoveries

#### Automatic Detection
1. **Discovery Alerts**: System automatically detects objects of interest
2. **Confidence Scores**: Review AI confidence levels (0-100%)
3. **Location Details**: Precise coordinates and altitude
4. **Investigation Status**: Track progress of investigations

#### Manual Review Process
1. **Review Evidence**: Examine photos/videos from detection
2. **Verify Findings**: Confirm if discovery requires action
3. **Coordinate Response**: Alert ground teams if needed
4. **Update Status**: Mark discoveries as verified or false positive

### Emergency Procedures

#### Emergency Stop
1. **Immediate Halt**: Click "Emergency Stop" button
2. **All Drones Stop**: Every drone will hover in place
3. **Status Update**: Mission status changes to "emergency_stop"
4. **Manual Override**: Take manual control if needed

#### Return to Home
1. **Individual Drone RTH**: Select specific drone and click "Return Home"
2. **All Drones RTH**: Use "Emergency Return" for all drones
3. **Safe Landing**: Drones will navigate to home position and land

#### Weather-Related Emergencies
1. **Weather Monitoring**: System tracks wind, visibility, temperature
2. **Automatic Pausing**: Mission pauses if conditions become unsafe
3. **Manual Override**: Force mission continuation if conditions allow

## Advanced Features

### Multi-Drone Coordination

#### Intelligent Assignment
- **Automatic Division**: System divides search areas optimally
- **Workload Balancing**: Distributes work based on drone capabilities
- **Collision Avoidance**: Ensures safe drone separation

#### Coordination Strategies
- **Sequential Search**: One area at a time for thorough coverage
- **Parallel Search**: Multiple areas simultaneously for speed
- **Priority-Based**: Focus on high-probability areas first

### AI-Powered Adaptations

#### Real-time Adjustments
- **Weather Adaptation**: Adjusts patterns for wind conditions
- **Battery Optimization**: Reroutes based on remaining power
- **Discovery Response**: Redirects drones to promising areas

#### Learning from Experience
- **Performance Analysis**: Tracks successful search patterns
- **Optimization**: Improves future mission planning
- **Custom Profiles**: Adapts to specific drone capabilities

### Analytics and Reporting

#### Mission Analytics
- **Coverage Efficiency**: Area covered vs time spent
- **Discovery Rates**: Success rates for different conditions
- **Performance Trends**: Improvement over time
- **Resource Utilization**: Optimal drone usage patterns

#### Report Generation
1. **Mission Reports**: Detailed summaries of each operation
2. **Performance Reports**: Analytics and improvement suggestions
3. **Incident Reports**: Documentation for legal/insurance purposes
4. **Training Reports**: Data for operator training programs

## Troubleshooting

### Common Issues

#### Connection Problems
- **WebSocket Issues**: Check firewall settings and port 8000 access
- **Database Errors**: Verify PostgreSQL is running and accessible
- **AI Service**: Ensure Ollama is running with correct model

#### Drone Communication
- **Signal Loss**: Check antenna positioning and interference
- **Battery Warnings**: Monitor levels and plan for battery swaps
- **GPS Issues**: Verify satellite visibility and accuracy

#### Performance Issues
- **Slow Response**: Check system resources and database performance
- **Memory Usage**: Monitor RAM usage and restart services if needed
- **Disk Space**: Ensure adequate storage for logs and media

### Getting Help

#### System Health Check
1. Visit http://localhost:8000/health
2. Check all service statuses
3. Review error logs in backend/logs/

#### Log Analysis
```bash
# View recent logs
docker compose logs -f backend

# Check specific service
docker compose logs frontend

# View error logs only
docker compose logs --tail=100 backend | grep ERROR
```

#### Database Issues
```bash
# Check database health
docker compose exec db pg_isready -U postgres

# View database logs
docker compose logs db

# Reset database (development only)
docker compose down -v
docker compose up -d db
```

## Best Practices

### Mission Planning
- **Detailed Descriptions**: Provide specific location and objective details
- **Environmental Awareness**: Consider weather and lighting conditions
- **Safety First**: Always prioritize safety over speed
- **Contingency Planning**: Plan for equipment failures and emergencies

### Operational Procedures
- **Regular Monitoring**: Check system status throughout missions
- **Battery Management**: Monitor and replace batteries proactively
- **Communication**: Maintain clear communication with ground teams
- **Documentation**: Record all significant events and decisions

### Maintenance
- **Regular Updates**: Keep software and firmware current
- **Hardware Checks**: Inspect drones before each mission
- **Data Backup**: Regularly backup mission data and logs
- **Training**: Conduct regular operator training sessions

## Keyboard Shortcuts

### General Navigation
- **Ctrl/Cmd + K**: Open command palette
- **Ctrl/Cmd + N**: New mission
- **Ctrl/Cmd + S**: Save current state
- **F5**: Refresh dashboard

### Mission Control
- **Space**: Emergency stop (when mission active)
- **R**: Return drones to home
- **P**: Pause/resume mission
- **Esc**: Cancel current action

### Chat Interface
- **Enter**: Send message
- **Shift + Enter**: New line (multiline messages)
- **Ctrl + L**: Clear chat history

## Mobile Usage

### Responsive Design
- The interface adapts to mobile screens
- Touch gestures supported for map interaction
- Simplified layouts for smaller screens

### Mobile-Specific Features
- **Swipe Navigation**: Swipe between dashboard sections
- **Touch Area Selection**: Tap and drag to select search areas
- **Vibration Alerts**: Haptic feedback for critical notifications
- **Offline Mode**: Limited functionality when network unavailable

## Integration with External Systems

### Ground Team Coordination
- **Real-time Location Sharing**: Share discovery locations with ground teams
- **Communication Integration**: Connect with existing radio systems
- **GPS Navigation**: Export coordinates for ground team navigation
- **Status Updates**: Automatic updates on mission progress

### Emergency Services Integration
- **Automatic Alerts**: Notify emergency services of critical discoveries
- **Data Sharing**: Share mission data with other agencies
- **Incident Reporting**: Generate reports for official records
- **Multi-agency Coordination**: Support for joint operations

## Security and Privacy

### Data Protection
- **Encryption**: All data encrypted in transit and at rest
- **Access Control**: Role-based permissions for different users
- **Audit Logging**: Complete record of all system activities
- **Data Retention**: Configurable policies for data storage

### Operational Security
- **Secure Communication**: Encrypted drone communication
- **Access Logging**: Track all user activities
- **Emergency Access**: Override controls for authorized personnel
- **Data Sanitization**: Secure deletion of sensitive mission data

## Performance Optimization

### System Tuning
- **Database Optimization**: Regular maintenance and indexing
- **Memory Management**: Configure appropriate resource limits
- **Network Optimization**: Optimize for low-bandwidth scenarios
- **Caching**: Intelligent caching for frequently accessed data

### Operational Efficiency
- **Mission Templates**: Save and reuse successful mission configurations
- **Automated Routines**: Schedule regular system maintenance
- **Performance Monitoring**: Track and optimize system performance
- **Resource Planning**: Optimal allocation of drones and personnel

---

## Quick Reference

### Emergency Contacts
- **Emergency Stop**: Space bar or Emergency Stop button
- **Ground Team**: [Your emergency contact info]
- **Technical Support**: [Your support contact info]

### Key Metrics to Monitor
- **System Health**: All services green
- **Drone Status**: All drones online with >20% battery
- **Mission Progress**: >80% coverage for active missions
- **Discovery Response**: <5 minutes from detection to investigation

### Daily Checklist
- [ ] System health check
- [ ] Drone battery levels
- [ ] Mission status review
- [ ] Data backup verification
- [ ] Weather condition check

---

**Remember: Safety first, thoroughness second, speed third.**