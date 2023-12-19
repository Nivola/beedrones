# SPDX-License-Identifier: EUPL-1.2
#
# (C) Copyright 2020-2022 Regione Piemonte
# (C) Copyright 2018-2023 CSI-Piemonte

from beecell.simple import truncate
from beedrones.grafana.client_grafana import GrafanaEntity


class GrafanaAlertNotification(GrafanaEntity):
    def get(self, alert_notification_uid=None):
        """Get grafana alert_notification

        :param alert_notification_id: alert_notification_id
        :return: alert_notification
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.notifications.get_channel_by_uid(alert_notification_uid)
        self.logger.debug("get alert notification: %s" % truncate(res))
        return res

    def get_by_name(self, account_name):
        """Get grafana alert_notification

        :param alert_notification_id: alert_notification_id
        :return: alert_notification
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.notifications.lookup_channels()
        self.logger.debug("get alert notification: %s" % truncate(res))

        if len(res) == 0:
            return None
        else:
            for alert in res:
                name = alert["name"]
                self.logger.debug("get alert notification - name: %s" % name)
                if name == account_name:
                    return alert

        return None

    def list(self):
        """List grafana alert_notifications

        :return: alert_notifications
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.notifications.get_channels()
        self.logger.debug("get alert notifications: %s" % truncate(res))
        return res

    def add(self, alert_name, email, **params):
        """Add grafana alert_notification

        :param str alert_notification_name: Name of this alert_notification.
        :return: alert_notification
        :raise GrafanaError:
        """
        data_alert_notification = {
            "name": alert_name,
            "type": "email",
            "isDefault": False,
            "sendReminder": False,
            "frequency": "",
            "settings": {
                "addresses": email,
                "autoResolve": True,
                "httpMethod": "POST",
                "uploadImage": True,
            },
        }
        res = self.manager.grafanaFace.notifications.create_channel(channel=data_alert_notification)
        self.logger.debug("add alert_notification: %s" % truncate(res))

        uid = res["uid"]
        self.logger.debug("alert_name: %s - uid: %s" % (alert_name, uid))
        return res

    def update(self, alert_notification_uid, account_name, email, **params):
        """Update grafana alert_notification

        :param str alert_notification_uid: Alert uuid.
        :param str account_name: Name of account.
        :param str email: Accoint email.
        :return: alert_notification
        :raise GrafanaError:
        """
        data_alert_notification = {
            "uid": alert_notification_uid,
            "name": account_name,
            "type": "email",
            "isDefault": False,
            "sendReminder": False,
            "frequency": "",
            "settings": {
                "addresses": email,
                "autoResolve": True,
                "httpMethod": "POST",
                "uploadImage": True,
            },
        }
        res = self.manager.grafanaFace.notifications.update_channel_by_uid(
            uid=alert_notification_uid, channel=data_alert_notification
        )
        self.logger.debug("add alert_notification: %s" % truncate(res))

        uid = res["uid"]
        self.logger.debug("account_name: %s - uid: %s" % (account_name, uid))
        return res

    def delete(self, alert_notification_uid):
        """Delete grafana alert_notification

        :param alert_notification_id: grafana alert_notification_id
        :return: True
        :raise GrafanaError:
        """
        res = self.manager.grafanaFace.notifications.delete_notification_by_uid(notification_uid=alert_notification_uid)
        return True
