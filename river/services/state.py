from django.db.models import Q
from river.models import FORWARD, BACKWARD
from river.models.approvement import Approvement
from river.models.state import State
from river.utils.exceptions import RiverException

__author__ = 'ahmetdal'


class StateService:
    def __init__(self):
        pass

    @staticmethod
    def get_state_by(**kwargs):
        if kwargs:
            return State.objects.get(**kwargs)

    @staticmethod
    def get_current_state(workflow_object, field):
        return getattr(workflow_object, field)

    @staticmethod
    def get_available_states(workflow_object, field, user, include_user=True):
        current_state = getattr(workflow_object, field)
        approvements = Approvement.objects.filter(
            field=field,
            workflow_object=workflow_object,
            meta__transition__source_state=current_state,
        )
        if include_user:
            approvements = approvements.filter(
                meta__permissions__in=user.user_permissions.all()
            )
        destination_states = approvements.values_list('meta__transition__destination_state', flat=True)
        return State.objects.filter(pk__in=destination_states)

    @staticmethod
    def get_inital_state(content_type, field):
        """
        A state which is not a destination of a transition but can be source of a transition OR not (a destination of a transition and this transition direction is FORWARD)
        """
        initial_state_candidates = State.objects.filter(
            Q(transitions_as_source__isnull=False,
              transitions_as_source__content_type=content_type,
              transitions_as_source__field=field,
              transitions_as_destination__isnull=True,
              ) &
            ~Q(
                transitions_as_destination__isnull=False,
                transitions_as_destination__direction=FORWARD,
                transitions_as_destination__content_type=content_type,
                transitions_as_destination__field=field
            )
        ).distinct()
        c = initial_state_candidates.count()
        if c == 0:
            raise RiverException('There is no available initial state for the content type %s. ' % content_type)
        elif c > 1:
            raise RiverException('There are multiple initial state for the content type %s. Have only one initial state' % content_type)

        return initial_state_candidates[0]

    @staticmethod
    def get_final_states(content_type, field):
        """
        A state which is not a source of a transition but can be destination of a transition OR not (a source of a transition and this transition direction is FORWARD)
        """
        final_states = State.objects.filter(
            Q(transitions_as_source__isnull=True,
              transitions_as_destination__isnull=False,
              transitions_as_destination__content_type=content_type,
              transitions_as_destination__field=field
              ) &
            ~Q(
                transitions_as_source__isnull=False,
                transitions_as_source__direction=FORWARD,
                transitions_as_source__content_type=content_type,
                transitions_as_source__field=field
            )
        ).distinct()
        c = final_states.count()
        if c == 0:
            raise RiverException('There is no available final state for the content type %s.' % content_type)

        return final_states
